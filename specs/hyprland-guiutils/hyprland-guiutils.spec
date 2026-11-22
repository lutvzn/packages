Name:           hyprland-guiutils
Version:        0.2.2
Release:        1%{?dist}
Summary:        Hyprland GUI utilities (dialogs, run prompt, welcome screen)
License:        BSD-3-Clause
URL:            https://github.com/hyprwm/hyprland-guiutils
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  pkgconfig(hyprlang) >= 0.6.0
BuildRequires:  pkgconfig(hyprtoolkit) >= 0.4.0
BuildRequires:  pkgconfig(hyprutils) >= 0.10.2
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(xkbcommon)

# Hyprland warns at startup when these are missing, and uses hyprland-dialog for
# its "app not responding" and permission prompts.
Supplements:    hyprland

%description
Small GUI programs Hyprland calls: hyprland-dialog, hyprland-run,
hyprland-welcome, hyprland-update-screen and hyprland-donate-screen.

%prep
%autosetup -p1

%build
%cmake -DCMAKE_BUILD_TYPE=Release
%cmake_build

%install
%cmake_install

%files
%license LICENSE
%{_bindir}/hyprland-dialog
%{_bindir}/hyprland-donate-screen
%{_bindir}/hyprland-run
%{_bindir}/hyprland-update-screen
%{_bindir}/hyprland-welcome
