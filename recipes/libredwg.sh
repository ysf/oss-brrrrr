#!/bin/sh
set -eu
sh ./autogen.sh
./configure --enable-shared --enable-static --disable-bindings --disable-json --enable-release
make -C src -j2 V=1 libredwg.la
mkdir build
cc $CFLAGS -Iinclude -Isrc -c examples/llvmfuzz.c -o build/llvmfuzz.o
c++ $CXXFLAGS "$HARNESS_MAIN" build/llvmfuzz.o src/.libs/libredwg.a \
  $LDFLAGS -lpcre2-8 -lm -o "$2"
