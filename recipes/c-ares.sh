#!/bin/sh
set -eu
cmake -S . -B build \
  -DCARES_SHARED=ON -DCARES_STATIC=OFF -DCARES_INSTALL=OFF \
  -DCARES_BUILD_TESTS=OFF -DCARES_BUILD_TOOLS=OFF \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --target c-ares --parallel 2 --verbose
