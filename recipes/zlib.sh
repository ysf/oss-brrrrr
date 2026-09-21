#!/bin/sh
set -eu
./configure --shared
make -j2 "$1" libz.a
mkdir -p "$(dirname "$2")"
c++ $CXXFLAGS -std=c++11 -I. "$HARNESS_SOURCES/zlib_uncompress_fuzzer.cc" \
  "$HARNESS_MAIN" libz.a $LDFLAGS -o "$2"
