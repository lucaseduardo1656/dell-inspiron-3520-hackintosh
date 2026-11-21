#!/usr/bin/env bash
# Build RealtekBluetoothFirmware v1.0.2 with the patch for the Inspiron 3520 Bluetooth chip
# (Realtek USB 0bda:c829). The patch comes from the reference repository
# pedrovrs301-gif/dell-inspiron-3520-i5-1235u-sequoia.
#
# macOS only. Needs the Xcode Command Line Tools (xcode-select --install), not full Xcode.
# Run scripts/fetch-components.sh first, then build the EFI again afterwards.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/downloads/realtek-bt-src"
PATCH="$ROOT/downloads/ref-inspiron3520/template/GitHub-Dell-Inspiron-3520/patches/RealtekBluetoothFirmware-v1.0.2-dell-c829.patch"
[ "$(uname)" = Darwin ] || { echo "macOS only"; exit 1; }
[ -d "$SRC/.git" ] && [ -f "$PATCH" ] || { echo "run scripts/fetch-components.sh first"; exit 1; }
if ! grep -q 0bda_c829 "$SRC/RealtekBluetoothFirmware/Info.plist"; then
  git -C "$SRC" apply "$PATCH"
fi
make -C "$SRC"
plutil -p "$SRC/build/RealtekBluetoothFirmware.kext/Contents/Info.plist" | grep -q '"idProduct" => 51241' \
  && echo "ok: kext matches 0bda:c829 ($SRC/build/RealtekBluetoothFirmware.kext)"
