#!/bin/sh
set -eu
cmake -S . -B build \
  -DBUILD_SHARED_LIBS=ON -DHB_BUILD_UTILS=OFF \
  -DHB_HAVE_FREETYPE=OFF -DHB_HAVE_GRAPHITE2=OFF -DHB_HAVE_GLIB=OFF \
  -DHB_HAVE_ICU=OFF -DHB_HAVE_GOBJECT=OFF -DHB_HAVE_INTROSPECTION=OFF
cmake --build build --target harfbuzz-subset --parallel 2 --verbose
cmake -S . -B harness-build \
  -DBUILD_SHARED_LIBS=OFF -DHB_BUILD_UTILS=OFF \
  -DHB_HAVE_FREETYPE=OFF -DHB_HAVE_GRAPHITE2=OFF -DHB_HAVE_GLIB=OFF \
  -DHB_HAVE_ICU=OFF -DHB_HAVE_GOBJECT=OFF -DHB_HAVE_INTROSPECTION=OFF
cmake --build harness-build --target harfbuzz-subset --parallel 2 --verbose
c++ $CXXFLAGS -Isrc test/fuzzing/hb-subset-fuzzer.cc "$HARNESS_MAIN" \
  harness-build/libharfbuzz-subset.a harness-build/libharfbuzz.a \
  $LDFLAGS -pthread -lm -o "$2"
