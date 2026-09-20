#!/bin/sh
set -eu
flags="-Wall -Wno-array-bounds -Wno-format-truncation $CFLAGS -D_GNU_SOURCE -DCONFIG_VERSION=\\\"$(cat VERSION)\\\" -DCONFIG_BIGNUM"
make -j2 CONFIG_LTO= CFLAGS="$flags" \
  .obj/quickjs.pic.o .obj/libregexp.pic.o .obj/libunicode.pic.o \
  .obj/cutils.pic.o .obj/quickjs-libc.pic.o .obj/libbf.pic.o
gcc -shared $LDFLAGS -o "$1" \
  .obj/quickjs.pic.o .obj/libregexp.pic.o .obj/libunicode.pic.o \
  .obj/cutils.pic.o .obj/quickjs-libc.pic.o .obj/libbf.pic.o -lm -ldl
