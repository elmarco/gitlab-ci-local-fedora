#!/bin/bash
# Regenerate the vendored npm dependencies tarball (Source1) for the
# gitlab-ci-local RPM.
#
# The upstream project builds with bun, which is not available in Fedora.
# Neither is a usable JavaScript bundler or TypeScript compiler:
# nodejs-esbuild was retired from rawhide (F44/F45 still ship it), and
# nodejs-typescript has not been built since Fedora 34. Therefore this
# package vendors everything it needs to build:
#
#   - node_modules_prod/  the npm packages that are compiled into the
#                         application and installed with it (the runtime
#                         closure)
#   - node_modules_dev/   the TypeScript compiler (a build-only tool, it is
#                         never installed into the RPM)
#
# This script:
#   1. downloads the upstream release tarball (Source0)
#   2. installs the exact dependency versions pinned in upstream's bun.lock,
#      using the same bun version as upstream's release CI
#   3. bundles the application with esbuild (available on the *packaging*
#      machine only) to determine which packages are actually used at
#      runtime - that closure becomes node_modules_prod/
#   4. emits <name>-<version>-vendor.tar.xz and bundled-deps.txt in the
#      current directory
#
# Requirements: bash, curl, nodejs, esbuild, tar, xz, unzip.
# (bun itself is downloaded and used temporarily; it is not installed)
#
# Usage: ./generate-vendor-tarball.sh <version>

set -euo pipefail

VERSION="${1:?usage: $0 <upstream-version>}"
NAME=gitlab-ci-local
# Keep in sync with .github/workflows/release.yml of the tagged release.
BUN_VERSION=1.4.3
# Build-only tools vendored in node_modules_dev/ (not installed in the RPM).
DEV_PACKAGES="typescript"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
OUTDIR="$(pwd)"

# --- 1. upstream release tarball ---------------------------------------------
TARBALL="${NAME}-${VERSION}.tar.gz"
if [[ ! -f "$TARBALL" ]]; then
    curl -fL -o "$TARBALL" "https://github.com/firecow/${NAME}/archive/refs/tags/${VERSION}.tar.gz"
fi
tar xzf "$TARBALL" -C "$WORKDIR"
SRC="$WORKDIR/${NAME}-${VERSION}"

# --- 2. install exact dependency versions with bun ----------------------------
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)  BUN_ARCH=x64 ;;
    aarch64) BUN_ARCH=arm64 ;;
    *) echo "unsupported architecture: $ARCH" >&2; exit 1 ;;
esac
curl -fsSL -o "$WORKDIR/bun.zip" \
    "https://github.com/oven-sh/bun/releases/download/bun-v${BUN_VERSION}/bun-linux-${BUN_ARCH}.zip"
unzip -q "$WORKDIR/bun.zip" -d "$WORKDIR"
"$WORKDIR/bun-linux-${BUN_ARCH}/bun" install --frozen-lockfile --cwd "$SRC"

# --- 3. determine the runtime dependency closure ------------------------------
# Bundle with esbuild (packaging machine only) and analyze its metafile; the
# packages whose files were compiled in are exactly the runtime closure.
sed -i "s/\"version\": \"0.0.0\"/\"version\": \"${VERSION}\"/" "$SRC/package.json"
( cd "$SRC" && esbuild src/index.ts \
    --bundle --platform=node --target=node20 --format=esm \
    --outfile=dist/index.js --metafile=meta.json )

cat > "$WORKDIR/prune.cjs" <<'EOF'
// Analyze the esbuild metafile and split node_modules into:
//   node_modules_prod/  runtime closure (compiled into the application)
//   node_modules_dev/   build-only tools ($DEV_PACKAGES)
const fs = require("fs");
const path = require("path");

const [, , srcDir, metaFile, outBase, devPkgsArg] = process.argv;
const devPkgs = devPkgsArg ? devPkgsArg.split(",") : [];
const meta = JSON.parse(fs.readFileSync(metaFile, "utf8"));

const roots = new Set();
for (const input of Object.keys(meta.inputs)) {
    const rel = path.isAbsolute(input) ? path.relative(srcDir, input) : input;
    if (rel.startsWith("..")) continue;
    const parts = rel.split(path.sep);
    const nmIdx = parts.lastIndexOf("node_modules");
    if (nmIdx === -1) continue;
    // package name is 1 path segment, or 2 for @scoped packages
    const nameSegs = parts[nmIdx + 1].startsWith("@") ? 2 : 1;
    roots.add(parts.slice(0, nmIdx + 1 + nameSegs).join("/"));
}

const pkgs = [];
for (const root of [...roots].sort()) {
    const pj = JSON.parse(fs.readFileSync(path.join(srcDir, root, "package.json"), "utf8"));
    let license = pj.license;
    if (typeof license === "object") license = license.type;
    if (Array.isArray(license)) license = license.join(" or ");
    pkgs.push({ root, name: pj.name, version: pj.version, license: license || "UNKNOWN" });
}

// manifest of the runtime closure: name, version, license, node_modules path
const manifest = pkgs.map((p) => `${p.name}\t${p.version}\t${p.license}\t${p.root}`);
fs.mkdirSync(outBase, { recursive: true });
fs.writeFileSync(path.join(outBase, "bundled-deps.txt"), manifest.join("\n") + "\n");
console.log(`runtime packages: ${pkgs.length}`);

function copyPkg (root, destBase) {
    const dest = path.join(destBase, root.replace(/^node_modules[\\/]/, ""));
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.cpSync(path.join(srcDir, root), dest, { recursive: true, verbatimSymlinks: true });
}

const prodDir = path.join(outBase, "node_modules_prod");
const devDir = path.join(outBase, "node_modules_dev");
for (const p of pkgs) copyPkg(p.root, prodDir);

// build-only tools and their transitive dependencies
const devSeen = new Set();
function addDev (name) {
    if (devSeen.has(name)) return;
    devSeen.add(name);
    const pjPath = path.join(srcDir, "node_modules", name, "package.json");
    if (!fs.existsSync(pjPath)) throw new Error(`dev package not found: ${name}`);
    copyPkg(`node_modules/${name}`, devDir);
    const pj = JSON.parse(fs.readFileSync(pjPath, "utf8"));
    for (const dep of Object.keys(pj.dependencies ?? {})) addDev(dep);
}
for (const name of devPkgs) addDev(name);
console.log(`build-only packages: ${devSeen.size} (${[...devSeen].join(", ")})`);
EOF
node "$WORKDIR/prune.cjs" "$SRC" "$SRC/meta.json" "$WORKDIR/pruned" "$DEV_PACKAGES"

# --- 4. create the vendor tarball ---------------------------------------------
# The archive contains node_modules_prod/, node_modules_dev/ (and the
# manifest) at the top level, so that "%setup -q -a1" unpacks it directly
# into the source tree.
tar -C "$WORKDIR/pruned" -cJf "${OUTDIR}/${NAME}-${VERSION}-vendor.tar.xz" \
    --sort=name --numeric-owner --owner=0 --group=0 --mtime=@0 \
    node_modules_prod node_modules_dev bundled-deps.txt
cp "$WORKDIR/pruned/bundled-deps.txt" "$OUTDIR/"

echo
echo "Created ${NAME}-${VERSION}-vendor.tar.xz and bundled-deps.txt in ${OUTDIR}"
