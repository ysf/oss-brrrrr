#!/bin/sh
set -eu
sh ./autogen.sh
./configure --enable-static --enable-shared --disable-asm --disable-require-system-font-provider
make -C libass -j2 V=1
mkdir build
cc $CFLAGS -DASS_FUZZMODE=2 -DASSFUZZ_MAX_LEN=8192 -Ilibass \
  -c "$HARNESS_SOURCES/fuzz.c" -o build/libass_fuzzer.o
c++ $CXXFLAGS "$HARNESS_MAIN" build/libass_fuzzer.o libass/.libs/libass.a \
  $LDFLAGS $(pkg-config --libs freetype2 fribidi harfbuzz fontconfig) -lm -o "$2"
