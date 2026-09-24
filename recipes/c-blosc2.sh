#!/bin/sh
set -eu
cmake -S . -B build -DBUILD_SHARED=ON -DBUILD_STATIC=ON -DBUILD_TESTS=OFF \
  -DBUILD_BENCHMARKS=OFF -DBUILD_EXAMPLES=OFF -DBUILD_FUZZERS=ON \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --target blosc2_shared fuzz_decompress_frame --parallel 2 --verbose
