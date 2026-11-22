#!/usr/bin/bash
# Build every package in specs/, in dependency order.
#
# A package whose exact name-version-release is already published is downloaded
# from the repo instead, after checking it is signed with this repo's key, so only
# new or bumped specs get built. Bump Release when changing a spec without changing
# Version, or the change won't be built.
#
# New builds land in out/built/ (unsigned), downloaded ones in out/published/.
# Run it inside a clean Fedora container matching the target release, e.g.:
#   podman run --rm -v "$PWD:/src:Z" -w /src registry.fedoraproject.org/fedora:45 ./build.sh
set -euo pipefail
shopt -s nullglob

# Each package can only BuildRequire packages listed before it.
PACKAGES=(
    hyprutils
    hyprlang
    hyprwire
    hyprland-protocols
    hyprwayland-scanner
    aquamarine
    hyprcursor
    hyprgraphics
    hyprtoolkit
    hyprland
    xdg-desktop-portal-hyprland
)

root=$PWD
built=$root/out/built
published=$root/out/published
mkdir -p "$built" "$published"

. /etc/os-release
repo_url=${REPO_URL:-https://lutvzn.github.io/packages/fedora/$VERSION_ID/$(uname -m)}

dnf -y install --setopt=install_weak_deps=False \
    rpm-build rpmdevtools 'dnf5-command(builddep)'

# An rpm database holding only this repo's key, to check downloaded packages.
keyring=$root/out/keyring
mkdir -p "$keyring"
rpmdb --root "$keyring" --initdb
rpmkeys --root "$keyring" --import "$root/RPM-GPG-KEY-lutvzn-packages"

# Download every RPM the spec would build from the published repo. Fails if any
# of them is missing or isn't signed with this repo's key.
fetch_published() {
    local spec=$1 tmp rpm
    tmp=$(mktemp -d)
    for rpm in $(rpmspec -q --builtrpms --qf '%{name}-%{version}-%{release}.%{arch}.rpm\n' "$spec"); do
        if ! curl -fsSL -o "$tmp/$rpm" "$repo_url/$rpm" ||
           ! rpmkeys --root "$keyring" --checksig "$tmp/$rpm" | grep ': digests signatures OK$' >/dev/null; then
            rm -rf "$tmp"
            return 1
        fi
    done
    mv "$tmp"/*.rpm "$published/"
    rm -rf "$tmp"
}

for pkg in "${PACKAGES[@]}"; do
    dir=$root/specs/$pkg
    spec=$dir/$pkg.spec
    echo "::group::$pkg"

    if fetch_published "$spec"; then
        echo "$pkg is already published, not rebuilding it"
    else
        # Download sources and check them against the pinned checksums. Every
        # source must have a checksum, so nothing unreviewed gets built.
        spectool --get-files --directory "$dir" "$spec"
        for src in $(spectool --list-files "$spec" | awk '{print $2}'); do
            grep -q "  ${src##*/}\$" "$dir/sources" || { echo "No checksum for ${src##*/}" >&2; exit 1; }
        done
        (cd "$dir" && sha256sum --check --strict sources)

        dnf -y builddep --setopt=install_weak_deps=False "$spec"
        rpmbuild -bb "$spec" \
            --define "_sourcedir $dir" \
            --define "_topdir $root/rpmbuild" \
            --define "_rpmdir $built" \
            --define '_build_name_fmt %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm'

        # Debug info is not published, so don't keep it.
        rm -f "$built"/*-debuginfo-*.rpm "$built"/*-debugsource-*.rpm
    fi

    # Install everything so far so the next packages can build against it.
    dnf -y install --setopt=install_weak_deps=False "$built"/*.rpm "$published"/*.rpm

    echo "::endgroup::"
done
