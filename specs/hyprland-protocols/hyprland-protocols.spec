Name:           hyprland-protocols
Version:        0.8.0
Release:        1%{?dist}
Summary:        Wayland protocol extensions for Hyprland
License:        BSD-3-Clause
URL:            https://github.com/hyprwm/hyprland-protocols
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  cmake
BuildRequires:  gcc

%description
%{summary}.

# Only the -devel package is built, matching Fedora's naming. It is a build
# dependency and isn't needed at runtime.
%package        devel
Summary:        %{summary}

%description    devel
%{summary}.

%prep
%autosetup -p1

%build
%cmake
%cmake_build

%install
%cmake_install

%files devel
%license LICENSE
%{_datadir}/%{name}/
%{_datadir}/pkgconfig/%{name}.pc
