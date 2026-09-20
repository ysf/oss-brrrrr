#!/bin/sh
set -eu
./configure-linux.sh --default
make -C Common++ -j2 all CXXFLAGS="$CFLAGS -fPIC"
make -C Packet++ -j2 all CXXFLAGS="$CFLAGS -fPIC"
mkdir build
g++ -shared $LDFLAGS -Wl,--whole-archive Packet++/Lib/libPacket++.a Common++/Lib/Release/libCommon++.a -Wl,--no-whole-archive -o "$1"
