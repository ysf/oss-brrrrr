#!/bin/sh
set -eu
sh ./autogen.sh --disable-static --enable-shared --without-magick --without-lcms --without-OpenEXR --without-nifti --without-fftw --without-pangoft2 --without-tiff --without-jpeg --without-png --without-webp --without-heif --without-poppler --without-rsvg --without-openslide --without-matio --without-cfitsio --without-gsf --without-imagequant --without-quantizr
make -C libvips -j2 V=1
