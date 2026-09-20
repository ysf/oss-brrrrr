#!/bin/sh
set -eu
mkdir build
cc $CFLAGS -fPIC -Isrc/lib -c src/lib/lwan-template.c -o build/lwan-template.o
cc -shared $LDFLAGS -Wl,--version-script=src/lib/liblwan.sym build/lwan-template.o -o "$1"
