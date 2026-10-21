#!/bin/bash
# Build the gitlab-ci-local RPM locally.
#
# On a clean Fedora system:  sudo dnf install rpm-build esbuild git-core nodejs
# then run this script.
#
# This machine currently lacks the esbuild RPM (no sudo), so fall back to the
# npm-installed esbuild in ~/.npm-global (equivalent binary, same result).

set -euo pipefail
cd "$(dirname "$0")"

ESBUILD="$(command -v esbuild || true)"
if [[ -z "$ESBUILD" && -x "$HOME/.npm-global/bin/esbuild" ]]; then
    export PATH="$HOME/.npm-global/bin:$PATH"
fi

rpmbuild -ba --nodeps \
    --define "_sourcedir $(pwd)/SOURCES" \
    --define "_specdir $(pwd)" \
    --define "_builddir $(pwd)/BUILD" \
    --define "_rpmdir $(pwd)/RPMS" \
    --define "_srcrpmdir $(pwd)" \
    gitlab-ci-local.spec

# --nodeps is only needed when the esbuild RPM is not installed locally;
# in mock/koi (or with "dnf install esbuild") the build deps resolve normally.
