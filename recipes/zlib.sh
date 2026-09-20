#!/bin/sh
set -eu
./configure --shared
make -j2 "$1"
