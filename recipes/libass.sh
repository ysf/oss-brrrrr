#!/bin/sh
set -eu
sh ./autogen.sh
./configure --disable-static --enable-shared --disable-asm --disable-require-system-font-provider
make -C libass -j2 V=1
