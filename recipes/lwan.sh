#!/bin/sh
set -eu
mkdir build
cc $CFLAGS -fPIC -Isrc/lib -c src/lib/lwan-template.c -o build/lwan-template.o
cc -shared $LDFLAGS -Wl,--version-script=src/lib/liblwan.sym build/lwan-template.o -o "$1"
cmake -S . -B harness-build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build harness-build --target lwan --parallel 2 --verbose
c++ $CXXFLAGS -std=c++11 -Isrc/lib src/bin/fuzz/template_fuzzer.cc \
  "$HARNESS_MAIN" harness-build/src/lib/liblwan.a \
  $LDFLAGS -lpthread -lz -lm -ldl -o "$2"
