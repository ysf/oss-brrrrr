# oss-brrrrr

x86-64 binaries including debug symbols, but without sanitizers or fuzzing harnesses.

| Project | Crash type | Fix pattern | Versions | Download |
|---|---|---|---|---|
| zlib | — | — | 1.2.11–1.3.2 (6) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/zlib-releases-1.2.11-1.3.2) |
| lz4 | — | — | 1.9.3–1.10.0 (3) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/lz4-releases-1.9.3-1.10.0) |
| libpng | — | — | 1.6.50–1.6.58 (9) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/libpng-releases-1.6.50-1.6.58) |
| lwan | Heap buffer overflow | Off-by-one bounds check | OSS-Fuzz 19013 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/lwan-oss-fuzz-19013-parent-fix) |
| PcapPlusPlus | Heap buffer overflow | Bounded string search | v20.08–v21.05 (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/pcapplusplus-releases-20.08-21.05) |
| HarfBuzz | Heap buffer overflow | Off-by-one bounds check | 2.8.0–2.8.1 (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/harfbuzz-releases-2.8.0-2.8.1) |
| simdjson | Out-of-bounds read | Integer range validation | issue 1273 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/simdjson-oss-fuzz-1273-parent-fix) |
| wasm3 | Heap buffer overflow | Stack depth check | OSS-Fuzz 33318 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/wasm3-oss-fuzz-33318-parent-fix) |
| file | Heap buffer overflow | String length bound | OSS-Fuzz 1064 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/file-oss-fuzz-1064-parent-fix) |
| c-ares | Heap buffer overflow | Address family validation | OSS-Fuzz 15373 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/c-ares-oss-fuzz-15373-parent-fix) |
| QuickJS | Unknown read | Parser error handling | OSS-Fuzz 21404 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/quickjs-oss-fuzz-21404-parent-fix) |
| libass | Heap buffer overflow | Empty buffer handling | OSS-Fuzz 31301 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/libass-oss-fuzz-31301-parent-fix) |
| c-blosc2 | Heap buffer overflow | Frame header validation | OSS-Fuzz 46460 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/c-blosc2-oss-fuzz-46460-parent-fix) |
| LibreDWG | Heap buffer overflow | String length decoding | OSS-Fuzz 44481 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/libredwg-oss-fuzz-44481-parent-fix) |
| libvips | Heap buffer overflow | No isolated fix | OSS-Fuzz 46436 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/libvips-oss-fuzz-46436-parent-fix) |
| libjxl | Negative size parameter | Empty input handling | OSS-Fuzz 46243 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/libjxl-oss-fuzz-46243-parent-fix) |
| muparser | Heap buffer overflow | Parser state validation | OSS-Fuzz 23330 parent/fix snapshots (2) | [Release](https://github.com/ysf/oss-brrrrr/releases/tag/muparser-oss-fuzz-23330-parent-fix) |
