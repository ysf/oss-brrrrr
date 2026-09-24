#!/bin/sh
set -eu
cmake -S . -B build -DBUILD_SHARED_LIBS=ON -DENABLE_OPENMP=OFF -DENABLE_SAMPLES=OFF -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --target muparser -j2
cmake -S . -B harness-build -DBUILD_SHARED_LIBS=OFF -DENABLE_OPENMP=OFF \
  -DENABLE_SAMPLES=OFF -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build harness-build --target muparser -j2
c++ $CXXFLAGS -std=c++11 -Iinclude "$HARNESS_SOURCES/set_eval_fuzzer.cc" \
  "$HARNESS_MAIN" harness-build/libmuparser.a $LDFLAGS -o "$2"
