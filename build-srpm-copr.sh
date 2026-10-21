#!/bin/bash
# Build a dist-neutral SRPM suitable for COPR builds (all sources embedded,
# Release tag re-expands %{?dist} per chroot on the builders).
#
# COPR only auto-downloads Sources that carry a URL, so building from the
# bare spec fails for the local-only sources; upload the SRPM this script
# produces instead:
#     copr-cli build <user>/<project> gitlab-ci-local-<version>-1.src.rpm

set -euo pipefail
cd "$(dirname "$0")"

rpmbuild -bs --nodeps --define "dist %{nil}" \
    --define "_sourcedir $(pwd)/SOURCES" \
    --define "_specdir $(pwd)" \
    --define "_builddir $(pwd)/BUILD" \
    --define "_rpmdir $(pwd)/RPMS" \
    --define "_srcrpmdir $(pwd)" \
    gitlab-ci-local.spec
