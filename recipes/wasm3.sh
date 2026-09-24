#!/bin/sh
set -eu
cmake -S . -B build \
  -DBUILD_WASI=none -DBUILD_NATIVE=OFF \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_POSITION_INDEPENDENT_CODE=ON
cmake --build build --target m3 --parallel 2 --verbose
cc -shared $LDFLAGS -Wl,--whole-archive build/source/libm3.a \
  -Wl,--no-whole-archive -lm -o "$1"
cc $CFLAGS -Isource -c platforms/app_fuzz/fuzzer.c -o build/wasm3_fuzzer.o
c++ $CXXFLAGS "$HARNESS_MAIN" build/wasm3_fuzzer.o build/source/libm3.a \
  $LDFLAGS -lm -o "$2"
