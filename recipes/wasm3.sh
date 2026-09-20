#!/bin/sh
set -eu
cmake -S . -B build \
  -DBUILD_WASI=none -DBUILD_NATIVE=OFF \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_POSITION_INDEPENDENT_CODE=ON
cmake --build build --target m3 --parallel 2 --verbose
cc -shared $LDFLAGS -Wl,--whole-archive build/source/libm3.a \
  -Wl,--no-whole-archive -lm -o "$1"
