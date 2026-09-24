#!/bin/sh
set -eu
make -C lib -j2 "${1#lib/}" liblz4.a CFLAGS="$CFLAGS" BUILD_SHARED=yes BUILD_STATIC=yes V=1
make -C ossfuzz -j2 decompress_fuzzer LIB_FUZZING_ENGINE="$HARNESS_MAIN" \
  CFLAGS="$CFLAGS" CXXFLAGS="$CXXFLAGS" LDFLAGS="$LDFLAGS"
