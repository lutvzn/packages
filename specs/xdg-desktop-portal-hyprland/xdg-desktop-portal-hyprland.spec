Name:           xdg-desktop-portal-hyprland
Version:        1.5.0
Release:        1%{?dist}
Summary:        xdg-desktop-portal backend for Hyprland

# xdg-desktop-portal-hyprland: BSD-3-Clause
# protocols/wlr-foreign-toplevel-management-unstable-v1.xml: HPND-sell-variant
License:        BSD-3-Clause AND HPND-sell-variant
URL:            https://github.com/hyprwm/xdg-desktop-portal-hyprland
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  systemd-rpm-macros
BuildRequires:  pkgconfig(gbm)
BuildRequires:  pkgconfig(hyprland-protocols) >= 0.8.0
BuildRequires:  pkgconfig(hyprlang)
BuildRequires:  pkgconfig(hyprtoolkit) >= 0.6.0
BuildRequires:  pkgconfig(hyprutils)
BuildRequires:  pkgconfig(hyprwayland-scanner) >= 0.4.6
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libpipewire-0.3) >= 1.1.82
BuildRequires:  pkgconfig(libspa-0.2)
BuildRequires:  pkgconfig(sdbus-c++) >= 2.0.0
BuildRequires:  pkgconfig(uuid)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols) >= 1.39
BuildRequires:  pkgconfig(wayland-scanner)

Requires:       xdg-desktop-portal
# The Screenshot portal runs grim, and slurp for interactive and color picking.
Requires:       grim
Requires:       slurp

Supplements:    hyprland

%description
An xdg-desktop-portal backend for Hyprland: screen sharing with an output,
window and region picker, screenshots and global shortcuts.

%prep
%autosetup -p1
# Bundled git submodules; both come from packages instead.
rm -rf subprojects

%build
%cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
%cmake_build

%install
%cmake_install

%post
%systemd_user_post %{name}.service

%preun
%systemd_user_preun %{name}.service

%files
%license LICENSE
%{_bindir}/hyprland-share-picker
%{_libexecdir}/%{name}
%{_datadir}/xdg-desktop-portal/portals/hyprland.portal
%{_datadir}/dbus-1/services/org.freedesktop.impl.portal.desktop.hyprland.service
%{_userunitdir}/%{name}.service
