#!/bin/sh
set -eu
autoreconf -fi
./configure --enable-static --enable-shared
make -j2 V=1
mkdir build
c++ $CXXFLAGS -std=c++11 -Isrc "$HARNESS_SOURCES/magic_fuzzer.cc" \
  "$HARNESS_MAIN" src/.libs/libmagic.a $LDFLAGS \
  -l:libz.a -l:liblz4.a -l:libbz2.a -l:liblzma.a -l:libzstd.a -o "$2"
