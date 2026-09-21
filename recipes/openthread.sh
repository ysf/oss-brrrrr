#!/bin/sh
set -eu
./bootstrap
./configure \
  --enable-fuzz-targets \
  --enable-application-coap \
  --enable-application-coap-secure \
  --enable-border-agent \
  --enable-border-router \
  --enable-cert-log \
  --enable-channel-manager \
  --enable-channel-monitor \
  --enable-child-supervision \
  --enable-cli \
  --enable-commissioner \
  --enable-dhcp6-client \
  --enable-dhcp6-server \
  --enable-dns-client \
  --enable-diag \
  --enable-ecdsa \
  --enable-ftd \
  --enable-jam-detection \
  --enable-joiner \
  --enable-legacy \
  --enable-mac-filter \
  --enable-mtd-network-diagnostic \
  --enable-ncp \
  --with-ncp-bus=uart \
  --enable-raw-link-api \
  --enable-service \
  --enable-sntp-client \
  --enable-udp-forward \
  --disable-docs
make -j2 V=1 LIB_FUZZING_ENGINE="$HARNESS_MAIN" \
  CFLAGS="$CFLAGS -Wall -Wextra -Wshadow -std=c99 -pedantic-errors -D_BSD_SOURCE=1 -D_DEFAULT_SOURCE=1 -Wno-error" \
  CXXFLAGS="$CXXFLAGS -Wall -Wextra -Wshadow -std=gnu++98 -Wno-c++14-compat -fno-exceptions -D_BSD_SOURCE=1 -D_DEFAULT_SOURCE=1 -Wno-error"
mkdir build harness-build
c++ -shared -Wl,--whole-archive src/core/libopenthread-ftd.a \
  -Wl,--no-whole-archive $LDFLAGS -o "$1"
cp tests/fuzz/ncp-uart-received-fuzzer "$2"
