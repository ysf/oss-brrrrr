#!/bin/sh
set -eu
cmake -S . -B build \
  -DPNG_SHARED=ON -DPNG_STATIC=OFF -DPNG_TESTS=OFF -DPNG_TOOLS=OFF \
  -DZLIB_INCLUDE_DIR="$DEPENDENCY_PREFIX/include" \
  -DZLIB_LIBRARY="$DEPENDENCY_PREFIX/lib/libz.so" \
  -DCMAKE_SKIP_RPATH=ON
cmake --build build --target png_shared --parallel 2 --verbose
