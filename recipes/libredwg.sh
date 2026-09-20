#!/bin/sh
set -eu
sh ./autogen.sh
./configure --enable-shared --disable-static --disable-bindings --disable-json --enable-release
make -C src -j2 V=1 libredwg.la
