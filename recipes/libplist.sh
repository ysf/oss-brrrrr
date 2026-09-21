#!/bin/sh
set -eu
printf '%s\n' 2.2.0 > .tarball-version
./autogen.sh --without-cython --without-tests --enable-static --enable-shared
make -j2 V=1
mkdir harness-build
c++ $CXXFLAGS -std=c++11 -Iinclude fuzz/oplist_fuzzer.cc "$HARNESS_MAIN" \
  src/.libs/libplist-2.0.a $LDFLAGS -lpthread -lm -o "$2"
