#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
flutter_bin=${FLUTTER_BIN:-flutter}
export CMAKE_BUILD_PARALLEL_LEVEL=${CMAKE_BUILD_PARALLEL_LEVEL:-2}
for component in amogos-store amogos-installer onboarding; do
    (
        cd "$root/$component"
        "$flutter_bin" pub get
        "$flutter_bin" build linux --release --no-pub
    )
done
"$root/scripts/package.sh" "${1:-$root/dist}"
