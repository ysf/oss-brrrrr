#!/bin/sh
set -eu
make -C lib -j2 "${1#lib/}" CFLAGS="$CFLAGS" BUILD_SHARED=yes BUILD_STATIC=no V=1
