#!/usr/bin/env bash
set -euo pipefail
test "$(id -u)" -ne 0 || { echo 'Run makepkg as a regular user.' >&2; exit 1; }
export AMOGOS_APPS_ROOT
AMOGOS_APPS_ROOT=$(cd "$(dirname "$0")/.." && pwd)
export PKGDEST
PKGDEST=$(realpath -m "${1:-$AMOGOS_APPS_ROOT/dist}")
mkdir -p "$PKGDEST"
export MAKEFLAGS=-j2
for project in store installer onboarding system; do
    staging=$(mktemp -d)
    (
        trap 'rm -f "$staging/PKGBUILD" "$staging/post-install"' EXIT
        cp "$AMOGOS_APPS_ROOT/packaging/$project/PKGBUILD" "$staging/"
        if [[ $project == system ]]; then
            cp "$AMOGOS_APPS_ROOT/packaging/system/post-install" "$staging/"
        fi
        cd "$staging"
        makepkg --nodeps --noconfirm --clean --cleanbuild --force
    )
    rmdir "$staging"
done
