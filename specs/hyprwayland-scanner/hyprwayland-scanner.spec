Name:           hyprwayland-scanner
Version:        0.4.6
Release:        1%{?dist}
Summary:        A Hyprland implementation of wayland-scanner, in and for C++
License:        BSD-3-Clause
URL:            https://github.com/hyprwm/hyprwayland-scanner
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  pkgconfig(pugixml)

%description
%{summary}.

# Only the -devel package is built, matching Fedora's naming. It is a build
# dependency and isn't needed at runtime. Fedora's 0.4.2 generates code that
# GCC 16 rejects.
%package        devel
Summary:        %{summary}

%description    devel
%{summary}.

%prep
%autosetup -p1

%build
%cmake -DCMAKE_BUILD_TYPE=Release
%cmake_build

%install
%cmake_install

%files devel
%license LICENSE
%{_bindir}/%{name}
%{_libdir}/pkgconfig/%{name}.pc
%{_libdir}/cmake/%{name}/
