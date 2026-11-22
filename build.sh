#!/usr/bin/bash
# Build every package in specs/ into out/, in dependency order.
# Run it inside a clean Fedora container matching the target release, e.g.:
#   podman run --rm -v "$PWD:/src:Z" -w /src registry.fedoraproject.org/fedora:45 ./build.sh
set -euo pipefail

# Each package can only BuildRequire packages listed before it.
PACKAGES=(
    hyprutils
    hyprlang
    hyprwire
    hyprland-protocols
    aquamarine
    hyprcursor
    hyprgraphics
    hyprland
)

root=$PWD
out=$root/out
mkdir -p "$out"

dnf -y install --setopt=install_weak_deps=False \
    rpm-build rpmdevtools 'dnf5-command(builddep)'

for pkg in "${PACKAGES[@]}"; do
    dir=$root/specs/$pkg
    spec=$dir/$pkg.spec
    echo "::group::$pkg"

    # Download sources and check them against the pinned checksums. Every source
    # must have a checksum, so nothing unreviewed gets built.
    spectool --get-files --directory "$dir" "$spec"
    for src in $(spectool --list-files "$spec" | awk '{print $2}'); do
        grep -q "  ${src##*/}\$" "$dir/sources" || { echo "No checksum for ${src##*/}" >&2; exit 1; }
    done
    (cd "$dir" && sha256sum --check --strict sources)

    dnf -y builddep --setopt=install_weak_deps=False "$spec"
    rpmbuild -bb "$spec" \
        --define "_sourcedir $dir" \
        --define "_topdir $root/rpmbuild" \
        --define "_rpmdir $out" \
        --define '_build_name_fmt %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm'

    # Debug info is not published, so don't keep it.
    rm -f "$out"/*-debuginfo-*.rpm "$out"/*-debugsource-*.rpm

    # Install what was built so far so the next packages can build against it.
    dnf -y install --setopt=install_weak_deps=False "$out"/*.rpm

    echo "::endgroup::"
done
