Name:           hyprwire
Version:        0.3.1
Release:        1%{?dist}
Summary:        Fast and consistent wire protocol for IPC in the Hyprland ecosystem
License:        BSD-3-Clause
URL:            https://github.com/hyprwm/hyprwire
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  pkgconfig(hyprutils) >= 0.9.0
BuildRequires:  pkgconfig(libffi)
BuildRequires:  pkgconfig(pugixml)

%description
%{summary}.

%package        devel
Summary:        Development files and protocol scanner for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    devel
Development files and the hyprwire-scanner protocol generator for %{name}.

%prep
%autosetup -p1

%build
%cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
%cmake_build

%install
%cmake_install

%files
%license LICENSE
%{_libdir}/lib%{name}.so.*

%files devel
%{_bindir}/%{name}-scanner
%{_includedir}/%{name}/
%{_libdir}/lib%{name}.so
%{_libdir}/pkgconfig/%{name}.pc
%{_libdir}/pkgconfig/%{name}-scanner.pc
%{_libdir}/cmake/%{name}-scanner/
