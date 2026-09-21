#!/bin/sh
set -eu
cmake -S . -B build \
  -DCARES_SHARED=ON -DCARES_STATIC=ON -DCARES_INSTALL=OFF \
  -DCARES_BUILD_TESTS=OFF -DCARES_BUILD_TOOLS=OFF \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --target c-ares c-ares_static --parallel 2 --verbose
cc $CFLAGS -DCARES_STATICLIB -I. -Ibuild -c test/ares-test-fuzz.c \
  -o build/ares-test-fuzz.o
c++ $CXXFLAGS "$HARNESS_MAIN" build/ares-test-fuzz.o \
  build/lib/libcares_static.a $LDFLAGS -pthread -o "$2"
