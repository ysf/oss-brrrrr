#!/bin/sh
set -eu
sh ./autogen.sh --enable-static --enable-shared --without-magick --without-lcms --without-OpenEXR --without-nifti --without-fftw --without-pangoft2 --without-tiff --without-jpeg --without-png --without-webp --without-heif --without-poppler --without-rsvg --without-openslide --without-matio --without-cfitsio --without-gsf --without-imagequant --without-quantizr
make -C libvips -j2 V=1
mkdir build
c++ $CXXFLAGS -I. fuzz/thumbnail_fuzzer.cc "$HARNESS_MAIN" \
  libvips/.libs/libvips.a $LDFLAGS \
  $(pkg-config --cflags --libs glib-2.0 gobject-2.0 gmodule-2.0 libexif expat) \
  -lm -o "$2"
