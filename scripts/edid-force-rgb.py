#!/usr/bin/env python3
"""Create an EDID override that forces plain RGB 8 bpc on an HDMI TV or monitor.

Symptom: the external display has a pink/magenta cast or banding. WhateverXe 0.8.3 follows
the YCbCr and deep-colour (30/36-bit) support that the sink advertises in its EDID instead of
driving RGB 8 bpc (see WhateverXe issues #74 and #120). Hiding those claims fixes it.

The script reads the EDID of the connected external display (the one with a CEA-861
extension block) through ioreg, clears:
  - YCbCr 4:4:4 / 4:2:2 support (CEA extension, byte 3), and
  - deep colour DC_48/36/30bit and DC_Y444 (HDMI vendor-specific data block, byte 6),
fixes the checksums and writes <out>/DisplayVendorID-xxxx/DisplayProductID-yyyy.

Install, then reboot:
  sudo mkdir -p /Library/Displays/Contents/Resources/Overrides
  sudo cp -R <out>/DisplayVendorID-xxxx /Library/Displays/Contents/Resources/Overrides/
Undo: delete that DisplayVendorID-xxxx folder and reboot.
"""
import os, plistlib, re, subprocess, sys

out = sys.argv[1] if len(sys.argv) > 1 else "edid-override"
ioreg = subprocess.run(["ioreg", "-lw0"], capture_output=True, text=True).stdout
edids = [bytes.fromhex(h) for h in re.findall(r'"IODisplayEDID" = <([0-9a-f]+)>', ioreg)]
ext = [e for e in edids if len(e) >= 256 and e[128] == 0x02]  # CEA extension (TV/HDMI); the internal panel uses DisplayID
if len(ext) != 1:
    sys.exit(f"expected exactly one external display with a CEA extension, found {len(ext)}")
e = bytearray(ext[0])
vendor = (e[8] << 8) | e[9]
product = e[10] | (e[11] << 8)
name = next((bytes(e[i+5:i+18]).split(b"\n")[0].decode(errors="ignore").strip()
             for i in range(54, 126, 18) if e[i:i+4] == b"\x00\x00\x00\xfc"), "Display")
e[0x18] &= ~0x18 & 0xFF                     # base block: colour encoding -> RGB 4:4:4 only
for blk in range(1, e[126] + 1):
    b = blk * 128
    if e[b] != 0x02:                        # not a CEA-861 extension
        continue
    print(f"CEA byte 3: {e[b+3]:#04x} -> ", end="")
    e[b + 3] &= ~0x30 & 0xFF                # no YCbCr 4:4:4 / 4:2:2
    print(f"{e[b+3]:#04x}")
    i, end = b + 4, b + e[b + 2]            # data block collection
    while i < end:
        tag, ln = e[i] >> 5, e[i] & 0x1F
        if tag == 3 and ln >= 6 and e[i+1:i+4] == b"\x03\x0c\x00":   # HDMI VSDB (OUI 00-0C-03)
            print(f"HDMI VSDB flags: {e[i+6]:#04x} -> ", end="")
            e[i + 6] &= ~0x78 & 0xFF        # no DC_48bit / DC_36bit / DC_30bit / DC_Y444
            print(f"{e[i+6]:#04x}")
        i += 1 + ln
for blk in range(e[126] + 1):               # checksums
    b = blk * 128
    e[b + 127] = (-sum(e[b:b+127])) & 0xFF
d = os.path.join(out, f"DisplayVendorID-{vendor:x}")
os.makedirs(d, exist_ok=True)
path = os.path.join(d, f"DisplayProductID-{product:x}")
plistlib.dump({"DisplayProductName": f"{name} (RGB)", "DisplayVendorID": vendor,
               "DisplayProductID": product, "IODisplayEDID": bytes(e)}, open(path, "wb"))
print("override written to", path)
