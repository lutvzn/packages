# ffmpeg and ffprobe with H.264 and H.265 encoding (x264, x265), which Fedora's
# ffmpeg-free leaves out. x264 and x265 aren't in Fedora either, so they are built
# here as static libraries, and ffmpeg's own libraries are linked statically too.
# Only the two programs get installed, so nothing clashes with the libav*-free
# libraries the system already has. Every other codec, and VA-API, NVENC/NVDEC and
# Vulkan, comes from Fedora.

%global x264_commit b35605ace3ddf7c1a5d67a2eb553f034aef41d55
%global x265_version 4.2

# ffmpeg's and x265's hand-written assembly doesn't mix well with LTO.
%global _lto_cflags %{nil}

Name:           ffmpeg-full
Version:        9.1
Release:        1%{?dist}
Summary:        ffmpeg and ffprobe with H.264 and H.265 encoding
# ffmpeg is built with --enable-gpl; x264 and x265 are GPL-2.0-or-later.
License:        GPL-2.0-or-later
URL:            https://ffmpeg.org
# Signed by FFmpeg's release key, FCF9 86EA 15E6 E293 A564 4F10 B432 2F04 D676 58D8.
Source0:        https://ffmpeg.org/releases/ffmpeg-%{version}.tar.xz
# x264 has no releases; this is the head of its stable branch.
Source1:        https://code.videolan.org/videolan/x264/-/archive/%{x264_commit}/x264-%{x264_commit}.tar.bz2
Source2:        https://bitbucket.org/multicoreware/x265_git/downloads/x265_%{x265_version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  nasm
BuildRequires:  bzip2-devel
BuildRequires:  lame-devel
BuildRequires:  nv-codec-headers
BuildRequires:  vulkan-headers
BuildRequires:  pkgconfig(dav1d)
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(freetype2)
BuildRequires:  pkgconfig(fribidi)
BuildRequires:  pkgconfig(gnutls)
BuildRequires:  pkgconfig(harfbuzz)
BuildRequires:  pkgconfig(libass)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(liblzma)
BuildRequires:  pkgconfig(libva)
BuildRequires:  pkgconfig(libva-drm)
BuildRequires:  pkgconfig(libwebp)
BuildRequires:  pkgconfig(libxml-2.0)
BuildRequires:  pkgconfig(opus)
BuildRequires:  pkgconfig(SvtAv1Enc)
BuildRequires:  pkgconfig(vorbis)
BuildRequires:  pkgconfig(vorbisenc)
BuildRequires:  pkgconfig(vpx)
BuildRequires:  pkgconfig(zimg)
BuildRequires:  pkgconfig(zlib)

# Both install /usr/bin/ffmpeg.
Conflicts:      ffmpeg-free
Conflicts:      ffmpeg

%description
The ffmpeg and ffprobe command-line tools, built with x264 and x265 (8, 10 and
12-bit) for H.264 and H.265 encoding, dav1d, SVT-AV1, libvpx, Opus, LAME and
Vorbis, subtitles through libass, HTTPS through GnuTLS, and VA-API, NVENC/NVDEC
and Vulkan hardware acceleration.

%prep
%autosetup -n ffmpeg-%{version} -p1 -a1
# %%setup only takes one -a, so unpack x265 separately.
tar -xzf %{SOURCE2}

%build
%set_build_flags
deps=$PWD/deps

# x264, with every bit depth.
pushd x264-%{x264_commit}
./configure --prefix="$deps" --enable-static --enable-pic --disable-cli \
    --disable-opencl --extra-cflags="$CFLAGS" --extra-ldflags="$LDFLAGS"
%make_build
make install-lib-static
popd

# x265, as one library with 8, 10 and 12-bit encoders, the way upstream's
# build/linux/multilib.sh does it.
pushd x265_%{x265_version}
x265_cmake() {
    cmake -S source -B "$@" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_FLAGS_RELEASE=-DNDEBUG \
        -DCMAKE_CXX_FLAGS_RELEASE=-DNDEBUG \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DCMAKE_INSTALL_PREFIX="$deps" \
        -DLIB_INSTALL_DIR=lib \
        -DENABLE_SHARED=OFF \
        -DENABLE_CLI=OFF \
        -DENABLE_LIBNUMA=OFF \
        -DENABLE_PIC=ON
}
x265_cmake build-12 -DHIGH_BIT_DEPTH=ON -DMAIN12=ON -DEXPORT_C_API=OFF
cmake --build build-12 %{?_smp_mflags}
x265_cmake build-10 -DHIGH_BIT_DEPTH=ON -DEXPORT_C_API=OFF
cmake --build build-10 %{?_smp_mflags}
x265_cmake build-8 -DLINKED_10BIT=ON -DLINKED_12BIT=ON \
    -DEXTRA_LIB='x265_main10.a;x265_main12.a' -DEXTRA_LINK_FLAGS=-L.
cmake --build build-8 %{?_smp_mflags}
cmake --install build-8
ar -M <<AR
CREATE $deps/lib/libx265.a
ADDLIB build-8/libx265.a
ADDLIB build-10/libx265.a
ADDLIB build-12/libx265.a
SAVE
END
AR
popd

# The explicit --enable flags make configure fail if a dependency is missing,
# instead of quietly building without it.
PKG_CONFIG_PATH="$deps/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}" \
./configure \
    --prefix=%{_prefix} \
    --bindir=%{_bindir} \
    --datadir=%{_datadir}/ffmpeg \
    --optflags="%{build_cflags}" \
    --extra-ldflags="%{build_ldflags}" \
    --extra-libs='-lstdc++ -lm -lpthread -ldl' \
    --disable-shared \
    --enable-static \
    --enable-pic \
    --disable-stripping \
    --disable-doc \
    --disable-ffplay \
    --disable-sdl2 \
    --disable-xlib \
    --disable-libxcb \
    --enable-gpl \
    --enable-libx264 \
    --enable-libx265 \
    --enable-libdav1d \
    --enable-libsvtav1 \
    --enable-libvpx \
    --enable-libopus \
    --enable-libmp3lame \
    --enable-libvorbis \
    --enable-libwebp \
    --enable-libass \
    --enable-libfreetype \
    --enable-libfontconfig \
    --enable-libfribidi \
    --enable-libharfbuzz \
    --enable-libzimg \
    --enable-libxml2 \
    --enable-gnutls \
    --enable-vaapi \
    --enable-libdrm \
    --enable-ffnvcodec \
    --enable-nvenc \
    --enable-nvdec \
    --enable-vulkan
%make_build

%install
make DESTDIR=%{buildroot} install-progs install-data
cp -p x264-%{x264_commit}/COPYING COPYING.x264
cp -p x265_%{x265_version}/COPYING COPYING.x265

%check
# The encoders this package exists for must be there, and x264 and x265 must
# encode, including x265's linked-in 10-bit encoder.
./ffmpeg -hide_banner -encoders > encoders
for enc in libx264 libx265 libsvtav1 h264_vaapi hevc_vaapi h264_nvenc hevc_nvenc; do
    grep -q " $enc " encoders || { echo "Missing encoder $enc" >&2; exit 1; }
done
for args in '-c:v libx264' '-c:v libx265' '-c:v libx265 -pix_fmt yuv420p10le'; do
    ./ffmpeg -hide_banner -loglevel error -f lavfi -i testsrc=size=128x72:duration=0.2 \
        $args -f null -
done

%files
%license COPYING.GPLv2 LICENSE.md COPYING.x264 COPYING.x265
%doc README.md
%{_bindir}/ffmpeg
%{_bindir}/ffprobe
%{_datadir}/ffmpeg/
