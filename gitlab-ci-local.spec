# Spec for gitlab-ci-local
#
# The upstream project is a TypeScript application normally built with bun,
# and its npm dependencies are normally resolved by a bundler. Neither bun
# nor a usable bundler/TypeScript compiler exists in current Fedora
# (nodejs-esbuild was retired from rawhide; nodejs-typescript has not been
# built since Fedora 34), so this package vendors what it needs:
#
#   - Source1 bundles the runtime npm dependencies (node_modules_prod/,
#     created from upstream's own bun.lock and pruned to the packages the
#     application actually loads) and the TypeScript compiler
#     (node_modules_dev/, a build-only tool that is not installed).
#     Regenerate it with: ./generate-vendor-tarball.sh <VERSION>
#   - %%build transpiles the TypeScript sources with the vendored tsc
#     (noCheck: the dev-only @types/* packages are not vendored)
#   - the application is installed under _datadir with its node_modules
#     tree and a /usr/bin symlink, like a classic nodejs package
#
# Patch0 adds JSON import attributes so the sources also run under plain
# Node.js, not only inside bundlers (upstreamable).

Name:           gitlab-ci-local
Version:        4.76.1
# Note: %%autorelease is NOT used deliberately - it requires the rpmautospec
# macros to be resolvable at rebuild time (dist-git, or mock --buildsrpm with
# the rpmautospec plugin), which is not the case when e.g. COPR rebuilds an
# uploaded SRPM with mock --rebuild. Switch back once the package is imported
# into Fedora dist-git.
Release:        1%{?dist}
Summary:        Run GitLab CI pipelines locally, without pushing

License:        MIT AND ISC AND BSD-2-Clause AND BSD-3-Clause AND Apache-2.0
URL:            https://github.com/firecow/gitlab-ci-local
Source0:        %{url}/archive/%{version}/gitlab-ci-local-%{version}.tar.gz
Source1:        gitlab-ci-local-%{version}-vendor.tar.xz
# Man page written for Fedora; upstream does not ship one
Source2:        gitlab-ci-local.1
# License inventory of the bundled npm modules (Node.js guidelines)
Source3:        gitlab-ci-local-%{version}-bundled-licenses.txt
# Add JSON import attributes for plain Node.js compatibility
Patch0:         node-json-import-attributes.patch

BuildArch:      noarch

BuildRequires:  git-core
BuildRequires:  nodejs >= 20.19
# mock buildroots install with install_weak_deps=0; without the full ICU
# data nodejs segfaults in Intl.Segmenter (RHBZ #2548696)
BuildRequires:  nodejs-full-i18n

# node runtime for the application and its bundled modules
Requires:       nodejs >= 20.19
# rendering the --help table uses Intl.Segmenter (via string-width);
# nodejs segfaults without the full ICU data (RHBZ #2548696)
Requires:       nodejs-full-i18n
# jobs with an image: run in a container runtime (shell jobs run on the host)
Suggests:       moby-engine

# The application ships with its node_modules tree; the npm modules listed
# below are installed under %%{_datadir}/%%{name}/node_modules (see
# bundled-deps.txt in Source1 for the full inventory).
Provides:       bundled(nodejs-@nodelib-fs.scandir) = 2.1.5
Provides:       bundled(nodejs-@nodelib-fs.stat) = 2.0.5
Provides:       bundled(nodejs-@nodelib-fs.walk) = 1.2.8
Provides:       bundled(nodejs-@sec-ant-readable-stream) = 0.4.1
Provides:       bundled(nodejs-@sindresorhus-merge-streams) = 4.0.0
Provides:       bundled(nodejs-agent-base) = 6.0.2
Provides:       bundled(nodejs-ajv) = 8.20.0
Provides:       bundled(nodejs-ansi-escapes) = 7.3.0
Provides:       bundled(nodejs-ansi-regex) = 6.3.0
Provides:       bundled(nodejs-ansi-styles) = 6.2.3
Provides:       bundled(nodejs-asynckit) = 0.4.0
Provides:       bundled(nodejs-axios) = 1.20.0
Provides:       bundled(nodejs-base64url) = 3.0.1
Provides:       bundled(nodejs-braces) = 3.0.3
Provides:       bundled(nodejs-call-bind-apply-helpers) = 1.0.2
Provides:       bundled(nodejs-camelcase) = 9.0.0
Provides:       bundled(nodejs-chalk) = 6.0.0
Provides:       bundled(nodejs-chalk-template) = 1.1.2
Provides:       bundled(nodejs-checksum) = 1.0.0
Provides:       bundled(nodejs-cliui) = 9.0.1
Provides:       bundled(nodejs-string-width) = 7.2.0
Provides:       bundled(nodejs-emoji-regex) = 10.6.0
Provides:       bundled(nodejs-combined-stream) = 1.0.8
Provides:       bundled(nodejs-debug) = 4.4.3
Provides:       bundled(nodejs-deep-extend) = 0.6.0
Provides:       bundled(nodejs-delayed-stream) = 1.0.0
Provides:       bundled(nodejs-dotenv) = 18.0.4
Provides:       bundled(nodejs-dunder-proto) = 1.0.1
Provides:       bundled(nodejs-environment) = 1.1.0
Provides:       bundled(nodejs-es-define-property) = 1.0.1
Provides:       bundled(nodejs-es-errors) = 1.3.0
Provides:       bundled(nodejs-es-object-atoms) = 1.1.2
Provides:       bundled(nodejs-es-set-tostringtag) = 2.1.0
Provides:       bundled(nodejs-escalade) = 3.2.0
Provides:       bundled(nodejs-execa) = 10.0.1
Provides:       bundled(nodejs-fast-deep-equal) = 3.1.3
Provides:       bundled(nodejs-fast-glob) = 3.3.3
Provides:       bundled(nodejs-glob-parent) = 5.1.2
Provides:       bundled(nodejs-fast-uri) = 3.1.8
Provides:       bundled(nodejs-fastq) = 1.20.3
Provides:       bundled(nodejs-figures) = 6.1.0
Provides:       bundled(nodejs-fill-range) = 7.1.1
Provides:       bundled(nodejs-follow-redirects) = 1.16.0
Provides:       bundled(nodejs-form-data) = 4.0.6
Provides:       bundled(nodejs-fs-extra) = 11.4.1
Provides:       bundled(nodejs-function-bind) = 1.1.2
Provides:       bundled(nodejs-get-caller-file) = 2.0.5
Provides:       bundled(nodejs-get-east-asian-width) = 1.7.0
Provides:       bundled(nodejs-get-intrinsic) = 1.3.0
Provides:       bundled(nodejs-get-proto) = 1.0.1
Provides:       bundled(nodejs-get-stream) = 9.0.1
Provides:       bundled(nodejs-globby) = 16.2.4
Provides:       bundled(nodejs-ignore) = 7.0.10
Provides:       bundled(nodejs-gopd) = 1.2.0
Provides:       bundled(nodejs-graceful-fs) = 4.2.11
Provides:       bundled(nodejs-has-flag) = 5.0.1
Provides:       bundled(nodejs-has-symbols) = 1.1.0
Provides:       bundled(nodejs-has-tostringtag) = 1.0.2
Provides:       bundled(nodejs-hasown) = 2.0.4
Provides:       bundled(nodejs-https-proxy-agent) = 5.0.1
Provides:       bundled(nodejs-human-signals) = 8.0.1
Provides:       bundled(nodejs-is-extglob) = 2.1.1
Provides:       bundled(nodejs-is-glob) = 4.0.3
Provides:       bundled(nodejs-is-number) = 7.0.0
Provides:       bundled(nodejs-is-path-inside) = 4.0.0
Provides:       bundled(nodejs-is-plain-obj) = 4.1.0
Provides:       bundled(nodejs-is-stream) = 4.0.1
Provides:       bundled(nodejs-is-unicode-supported) = 2.1.0
Provides:       bundled(nodejs-js-yaml) = 5.4.2
Provides:       bundled(nodejs-json-schema-traverse) = 1.0.0
Provides:       bundled(nodejs-jsonfile) = 6.2.1
Provides:       bundled(nodejs-jsonpointer) = 5.0.1
Provides:       bundled(nodejs-math-intrinsics) = 1.1.0
Provides:       bundled(nodejs-merge2) = 1.4.1
Provides:       bundled(nodejs-micromatch) = 4.0.8
Provides:       bundled(nodejs-picomatch) = 2.3.2
Provides:       bundled(nodejs-mime-db) = 1.52.0
Provides:       bundled(nodejs-mime-types) = 2.1.35
Provides:       bundled(nodejs-ms) = 2.1.3
Provides:       bundled(nodejs-npm-run-path) = 6.0.0
Provides:       bundled(nodejs-path-key) = 4.0.0
Provides:       bundled(nodejs-unicorn-magic) = 0.3.0
Provides:       bundled(nodejs-object-traversal) = 1.0.1
Provides:       bundled(nodejs-p-map) = 7.0.8
Provides:       bundled(nodejs-parse-ms) = 4.0.0
Provides:       bundled(nodejs-pretty-hrtime) = 1.0.3
Provides:       bundled(nodejs-pretty-ms) = 9.3.1
Provides:       bundled(nodejs-proxy-from-env) = 2.1.0
Provides:       bundled(nodejs-queue-microtask) = 1.2.3
Provides:       bundled(nodejs-re2js) = 2.8.6
Provides:       bundled(nodejs-reusify) = 1.1.0
Provides:       bundled(nodejs-run-parallel) = 1.2.0
Provides:       bundled(nodejs-semver) = 7.8.5
Provides:       bundled(nodejs-signal-exit) = 4.1.0
Provides:       bundled(nodejs-slash) = 5.1.0
Provides:       bundled(nodejs-split2) = 4.2.0
Provides:       bundled(nodejs-string-width) = 8.3.0
Provides:       bundled(nodejs-strip-ansi) = 7.2.0
Provides:       bundled(nodejs-strip-final-newline) = 4.0.0
Provides:       bundled(nodejs-supports-color) = 10.2.2
Provides:       bundled(nodejs-supports-hyperlinks) = 4.5.0
Provides:       bundled(nodejs-terminal-link) = 5.0.0
Provides:       bundled(nodejs-to-regex-range) = 5.0.1
Provides:       bundled(nodejs-unicorn-magic) = 0.4.1
Provides:       bundled(nodejs-universalify) = 2.0.1
Provides:       bundled(nodejs-which-command) = 0.1.0
Provides:       bundled(nodejs-wrap-ansi) = 9.0.2
Provides:       bundled(nodejs-string-width) = 7.2.0
Provides:       bundled(nodejs-emoji-regex) = 10.6.0
Provides:       bundled(nodejs-y18n) = 5.0.8
Provides:       bundled(nodejs-yargs) = 18.2.0
Provides:       bundled(nodejs-yargs-parser) = 22.0.0
Provides:       bundled(nodejs-yoctocolors) = 2.2.0

%description
gitlab-ci-local runs .gitlab-ci.yml pipelines locally, directly on your
machine or in local containers, the same way a GitLab Runner would. It
parses the pipeline configuration, expands includes, variables and rules,
executes jobs (shell or docker executor), and supports artifacts, needs,
caches and much more - without pushing a single commit.

%prep
%setup -q -a1
%patch -P0 -p1

%build
# Upstream stamps the release version into package.json during its release
# process (see .github/workflows/release.yml); the git tag archive ships 0.0.0.
sed -i 's/"version": "0.0.0"/"version": "%{version}"/' package.json

# Transpile TypeScript with the vendored compiler. noCheck: the dev-only
# @types/* declarations are not vendored, only the emit is needed.
cat > tsconfig.build.json <<'TSEOF'
{
  "compilerOptions": {
    "target": "es2022",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "noCheck": true,
    "rootDir": "src",
    "outDir": "dist",
    "types": []
  },
  "include": ["src"]
}
TSEOF
node node_modules_dev/typescript/bin/tsc -p tsconfig.build.json

# make the runtime closure resolvable for %%check and the completion
# generation in %%install (only node_modules_prod is installed)
ln -s node_modules_prod node_modules

%check
node dist/index.js --version | grep -F '%{version}'

# Rendering the yargs help table goes through cliui -> string-width ->
# Intl.Segmenter, which segfaults inside nodejs when the full ICU data
# is missing (RHBZ #2548696). The nodejs-full-i18n Requires above covers
# this at runtime, the BuildRequires covers buildroots that install
# without weak dependencies (mock, COPR).
node dist/index.js --help > /dev/null

# Smoke test: parse a minimal pipeline inside a git repository.
mkdir smoke && cd smoke
git init -q -b main .
git config user.email builder@localhost
git config user.name builder
printf 'test-job:\n  script: echo hello\n' > .gitlab-ci.yml
git add .gitlab-ci.yml
git commit -qm init
node ../dist/index.js --list | grep test-job

%install
# bundled modules license inventory (see Node.js packaging guidelines)
cp -a %{SOURCE3} .

# Application: transpiled sources, the runtime node_modules tree (renamed
# from node_modules_prod) and package.json ("type": "module" for ESM).
install -d %{buildroot}%{_datadir}/%{name}
cp -a dist package.json %{buildroot}%{_datadir}/%{name}/
cp -a node_modules_prod %{buildroot}%{_datadir}/%{name}/node_modules

# the /usr/bin symlink target is executed directly via its shebang
chmod 0755 %{buildroot}%{_datadir}/%{name}/dist/index.js
install -d %{buildroot}%{_bindir}
ln -s ../share/%{name}/dist/index.js %{buildroot}%{_bindir}/%{name}

# drop empty placeholder files shipping inside npm packages
find %{buildroot}%{_datadir}/%{name}/node_modules -name '.gitkeep' -size 0 -delete

# zsh completion, generated by the application itself
node dist/index.js --completion > _%{name}
install -Dpm 0644 _%{name} %{buildroot}%{zsh_completions_dir}/_%{name}

# man page
install -Dpm 0644 %{SOURCE2} %{buildroot}%{_mandir}/man1/%{name}.1

%files
%license LICENSE %{name}-%{version}-bundled-licenses.txt
%doc README.md
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{zsh_completions_dir}/_%{name}
%{_mandir}/man1/%{name}.1*

%changelog
* Wed Oct 21 2026 Marc-André Lureau <marcandre.lureau@redhat.com> - 4.76.1-1
- Initial package
