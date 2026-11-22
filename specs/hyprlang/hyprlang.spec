Name:           hyprlang
Version:        0.6.8
Release:        1%{?dist}
Summary:        The official implementation library for the hypr config language
License:        LGPL-3.0-only
URL:            https://github.com/hyprwm/hyprlang
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  pkgconfig(hyprutils) >= 0.7.1

%description
%{summary}.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    devel
Development files for %{name}.

%prep
%autosetup -p1

%build
%cmake -DCMAKE_BUILD_TYPE=Release
%cmake_build

%install
%cmake_install

%files
%license LICENSE COPYRIGHT
%{_libdir}/lib%{name}.so.*

%files devel
%{_includedir}/%{name}.hpp
%{_libdir}/lib%{name}.so
%{_libdir}/pkgconfig/%{name}.pc
