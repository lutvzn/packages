%global glaze_version 7.2.0

Name:           hyprland
Version:        0.57.2
Release:        1%{?dist}
Summary:        Dynamic tiling Wayland compositor that doesn't sacrifice on its looks

# hyprland: BSD-3-Clause
# subprojects/udis86: BSD-2-Clause
# glaze (header-only, compiled in): MIT
# protocols/kde-server-decoration.xml: LGPL-2.1-or-later
# protocols/wlr-*.xml: HPND-sell-variant
License:        BSD-3-Clause AND BSD-2-Clause AND MIT AND LGPL-2.1-or-later AND HPND-sell-variant
URL:            https://github.com/hyprwm/Hyprland
Source0:        %{url}/releases/download/v%{version}/source-v%{version}.tar.gz
# Hyprland's CMake fetches glaze from git at build time; ship the release instead.
Source1:        https://github.com/stephenberry/glaze/archive/v%{glaze_version}/glaze-%{glaze_version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  python3
BuildRequires:  cmake(glslang)
BuildRequires:  pkgconfig(aquamarine) >= 0.15.0
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(egl)
BuildRequires:  pkgconfig(gbm)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  pkgconfig(glesv2)
BuildRequires:  pkgconfig(hyprcursor) >= 0.1.7
BuildRequires:  pkgconfig(hyprgraphics) >= 0.5.1
BuildRequires:  pkgconfig(hyprland-protocols) >= 0.8.0
BuildRequires:  pkgconfig(hyprlang) >= 0.6.7
BuildRequires:  pkgconfig(hyprutils) >= 0.14.3
BuildRequires:  pkgconfig(hyprwayland-scanner) >= 0.3.10
BuildRequires:  pkgconfig(hyprwire)
BuildRequires:  pkgconfig(hyprwire-scanner)
BuildRequires:  pkgconfig(lcms2)
BuildRequires:  pkgconfig(libcanberra)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libeis-1.0)
BuildRequires:  pkgconfig(libinput) >= 1.29
BuildRequires:  pkgconfig(lua) >= 5.5
BuildRequires:  pkgconfig(muparser)
BuildRequires:  pkgconfig(pango)
BuildRequires:  pkgconfig(pangocairo)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(re2)
BuildRequires:  pkgconfig(readline)
BuildRequires:  pkgconfig(uuid)
BuildRequires:  pkgconfig(wayland-protocols) >= 1.49
BuildRequires:  pkgconfig(wayland-scanner)
BuildRequires:  pkgconfig(wayland-server) >= 1.22.91
BuildRequires:  pkgconfig(xcb)
BuildRequires:  pkgconfig(xcb-composite)
BuildRequires:  pkgconfig(xcb-errors)
BuildRequires:  pkgconfig(xcb-icccm)
BuildRequires:  pkgconfig(xcb-render)
BuildRequires:  pkgconfig(xcb-res)
BuildRequires:  pkgconfig(xcb-xfixes)
BuildRequires:  pkgconfig(xcursor)
BuildRequires:  pkgconfig(xkbcommon) >= 1.11.0

# The bundled udis86 is a modified fork, so the Fedora package can't replace it.
Provides:       bundled(udis86) = 1.7.2
Provides:       bundled(glaze) = %{glaze_version}

Requires:       xorg-x11-server-Xwayland%{?_isa}

%description
Hyprland is a dynamic tiling Wayland compositor that doesn't sacrifice
on its looks. It supports multiple layouts, fancy effects, has a
very flexible IPC model allowing for a lot of customization and more.

This build leaves out hyprpm and the plugin headers, the UWSM session,
and the default wallpapers.

%prep
%autosetup -n %{name}-source -p1 -a1
rm -rf subprojects/tracy
cp -p subprojects/udis86/LICENSE LICENSE-udis86
cp -p glaze-%{glaze_version}/LICENSE LICENSE-glaze

%build
# hyprctl reports these; release tarballs have no git metadata.
export GIT_TAG=v%{version}
%cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DNO_HYPRPM=ON \
    -DNO_UWSM=ON \
    -DFETCHCONTENT_FULLY_DISCONNECTED=ON \
    -DFETCHCONTENT_SOURCE_DIR_GLAZE=$PWD/glaze-%{glaze_version}
%cmake_build

%install
%cmake_install
# CMake puts the user unit under the lib64 dir; systemd looks in /usr/lib.
mkdir -p %{buildroot}%{_userunitdir}
mv %{buildroot}%{_libdir}/systemd/user/hyprland-session.target %{buildroot}%{_userunitdir}/
rm -rf %{buildroot}%{_libdir}/systemd
# Plugin headers (no hyprpm) and glaze's own install rules.
rm -rf %{buildroot}%{_includedir} %{buildroot}%{_datadir}/pkgconfig \
       %{buildroot}%{_datadir}/glaze %{buildroot}%{_libdir}/cmake
# The 48 MB of default wallpapers. Hyprland falls back to a plain background,
# and shells like Noctalia draw their own.
rm -f %{buildroot}%{_datadir}/hypr/wall*.png

%files
%license LICENSE LICENSE-udis86 LICENSE-glaze
%{_bindir}/Hyprland
%{_bindir}/hyprland
%{_bindir}/hyprctl
%{_bindir}/start-hyprland
%{_datadir}/hypr/
%{_datadir}/wayland-sessions/%{name}.desktop
%{_datadir}/xdg-desktop-portal/%{name}-portals.conf
%{_userunitdir}/hyprland-session.target
%{_mandir}/man1/hyprctl.1*
%{_mandir}/man1/Hyprland.1*
