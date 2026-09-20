#!/bin/sh
set -eu
autoreconf -fi
./configure --disable-static --enable-shared
make -j2 V=1
