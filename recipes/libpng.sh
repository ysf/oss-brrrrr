#!/bin/sh
set -eu
cmake -S . -B build \
  -DPNG_SHARED=ON -DPNG_STATIC=ON -DPNG_TESTS=OFF -DPNG_TOOLS=OFF \
  -DZLIB_INCLUDE_DIR="$DEPENDENCY_PREFIX/include" \
  -DZLIB_LIBRARY="$DEPENDENCY_PREFIX/lib/libz.so" \
  -DCMAKE_SKIP_RPATH=ON
cmake --build build --target png_shared png_static --parallel 2 --verbose
c++ $CXXFLAGS -std=c++11 -I. -Ibuild contrib/oss-fuzz/libpng_read_fuzzer.cc \
  "$HARNESS_MAIN" build/libpng16.a "$DEPENDENCY_PREFIX/lib/libz.a" \
  $LDFLAGS -lm -o "$2"
