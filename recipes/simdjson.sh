#!/bin/sh
set -eu
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DSIMDJSON_JUST_LIBRARY=ON \
  -DSIMDJSON_BUILD_STATIC=OFF
cmake --build build --target simdjson --parallel 2 --verbose
