#!/bin/sh
set -eu
flags="-Wall -Wno-array-bounds -Wno-format-truncation $CFLAGS -D_GNU_SOURCE -DCONFIG_VERSION=\\\"$(cat VERSION)\\\" -DCONFIG_BIGNUM"
make -j2 CONFIG_LTO= CFLAGS="$flags" \
  .obj/quickjs.pic.o .obj/libregexp.pic.o .obj/libunicode.pic.o \
  .obj/cutils.pic.o .obj/quickjs-libc.pic.o .obj/libbf.pic.o
gcc -shared $LDFLAGS -o "$1" \
  .obj/quickjs.pic.o .obj/libregexp.pic.o .obj/libunicode.pic.o \
  .obj/cutils.pic.o .obj/quickjs-libc.pic.o .obj/libbf.pic.o -lm -ldl
mkdir build
cc $CFLAGS -I. -I"$HARNESS_SOURCES" -c "$HARNESS_SOURCES/fuzz_common.c" \
  -o build/fuzz_common.o
cc $CFLAGS -I. -I"$HARNESS_SOURCES" -c "$HARNESS_SOURCES/fuzz_compile.c" \
  -o build/fuzz_compile.o
c++ $CXXFLAGS "$HARNESS_MAIN" build/fuzz_common.o build/fuzz_compile.o \
  .obj/quickjs.pic.o .obj/libregexp.pic.o .obj/libunicode.pic.o \
  .obj/cutils.pic.o .obj/quickjs-libc.pic.o .obj/libbf.pic.o \
  $LDFLAGS -lm -ldl -o "$2"
