#!/bin/sh
set -eu
./configure --shared --prefix="$DEPENDENCY_PREFIX"
make -j2 "$1"
make install LDCONFIG=:
