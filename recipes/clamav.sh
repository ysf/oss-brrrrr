#!/bin/sh
set -eu
./configure \
  --disable-clamdtop \
  --disable-clamonacc \
  --disable-llvm \
  --disable-mempool \
  --disable-unrar \
  --enable-fuzz=yes \
  --enable-shared \
  --enable-static \
  --with-libjson=no \
  --with-openssl=/usr \
  --with-pcre=no \
  --with-xml=/usr
make -j2 V=1 -C libltdl
make -j2 V=1 -C libclamav
mkdir harness-build
c++ $CXXFLAGS -std=c++11 -DCLAMAV_FUZZ_OLE2 \
  -I. -Ishared -Ilibclamav fuzz/clamav_scanmap_fuzzer.cpp "$HARNESS_MAIN" \
  libclamav/.libs/libclamav.a libclamav/.libs/libclammspack.a $LDFLAGS \
  $(pkg-config --libs libxml-2.0) -lssl -lcrypto -lz -lbz2 -ldl -lpthread -lm -o "$2"
