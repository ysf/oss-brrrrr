#!/bin/sh
set -eu
cmake -S . -B build -DBUILD_SHARED_LIBS=ON -DENABLE_OPENMP=OFF -DENABLE_SAMPLES=OFF -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --target muparser -j2
