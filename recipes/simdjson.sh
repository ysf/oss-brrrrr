#!/bin/sh
set -eu
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DSIMDJSON_JUST_LIBRARY=ON \
  -DSIMDJSON_BUILD_STATIC=OFF
cmake --build build --target simdjson --parallel 2 --verbose
cmake -S . -B harness-build \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DSIMDJSON_JUST_LIBRARY=ON \
  -DSIMDJSON_BUILD_STATIC=ON
cmake --build harness-build --target simdjson --parallel 2 --verbose
c++ $CXXFLAGS -Iinclude -Ifuzz fuzz/fuzz_ondemand.cpp "$HARNESS_MAIN" \
  harness-build/libsimdjson.a $LDFLAGS -pthread -o "$2"
