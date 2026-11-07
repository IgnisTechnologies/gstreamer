#!/usr/bin/env bash
set -euo pipefail
BUILD_DIR="${1:-build-metadata-regressions}"
if [ ! -f "$BUILD_DIR/build.ninja" ]; then
  meson setup "$BUILD_DIR" -Dauto_features=disabled -Dbase=enabled -Dbad=enabled \
  -Dgood=disabled -Dugly=disabled -Dtools=enabled -Dtests=enabled -Dgstreamer:check=enabled -Dgstreamer:tools=enabled \
  -Dgst-plugins-bad:mpegtsmux=enabled
fi
BUILD_DIR="$(cd "$BUILD_DIR" && pwd)"
meson compile -C "$BUILD_DIR" gstmpegtsmux elements_mpegtsmux gst-plugin-scanner gstcoreelements
# An empty GST_CHECKS match must not turn a removed test into a green build.
list="$(meson devenv -C "$BUILD_DIR" "$BUILD_DIR/subprojects/gst-plugins-bad/tests/check/elements_mpegtsmux" --list-tests)"
for name in test_id3_metadata_alignment test_klv_metadata_alignment \
  test_id3_metadata_alignment_cbr test_klv_metadata_alignment_cbr; do
  printf '%s\n' "$list" | grep -Fx "Test: $name"
done
GST_CHECKS=test_id3_metadata_alignment,test_klv_metadata_alignment,test_id3_metadata_alignment_cbr,test_klv_metadata_alignment_cbr \
  meson test -C "$BUILD_DIR" --no-rebuild --print-errorlogs elements_mpegtsmux
