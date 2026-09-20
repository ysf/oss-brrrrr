#!/bin/sh
set -eu
cmake -S . -B build -DBUILD_SHARED=ON -DBUILD_STATIC=OFF -DBUILD_TESTS=OFF -DBUILD_BENCHMARKS=OFF -DBUILD_EXAMPLES=OFF -DBUILD_FUZZERS=OFF -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --target blosc2_shared --parallel 2 --verbose
