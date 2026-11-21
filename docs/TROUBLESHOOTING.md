# Troubleshooting

**English** · [Português](pt-BR/SOLUCAO-DE-PROBLEMAS.md)

Change one thing at a time, then rebuild the EFI (`rm -rf build && python3 scripts/build-efi.py`).
Build with `VERBOSE_BOOT=1` while debugging: the last lines on screen show where the boot stops.

Entries marked † did not happen on the tested laptop. They are suggestions taken from the
reference builds and the WhateverXe documentation.

## Boot

| Symptom | What to try |
|---|---|
| The OpenCore menu shows only another disk, no installer or recovery | Press Space to show hidden entries. This EFI sets `HideAuxiliary=false`. |
| Hangs at `[EB\|#LOG:EXITBS:START]` † | Booter quirks or memory map. Compare your BIOS settings with [INSTALL.md](INSTALL.md#3-bios-settings). |
| Black screen after the verbose log, but the laptop is still on † | Add `-wex-edp-keep` to the boot-args (used by the IdeaPad 3 build and the Sequoia reference). |
| Kernel panic mentioning `AMFI`, `IO80211` or `Skywalk` † | Disable the four Wi-Fi entries and the Skywalk block, install over a cable or tethering, then enable them again. |
| Kernel panic mentioning `WhateverXe` † | Remove `-igfxdvmt` and the iGPU `DeviceProperties`. |

## Graphics and displays

| Symptom | What to try |
|---|---|
| 7 MB VRAM, white desktop background, slow animations | Install the WhateverXe-Graphics package and restart. Check `ioreg -r -c AMFIAnchor -l` for `InstallStatus = 1`. |
| Screen went dark | Brightness was set to 0: the backlight is off, but the panel is not. Raise it from Control Center (Cmd+Space, type "Displays"). |
| HDMI display with a pink cast or banding | EDID override: [INSTALL.md, step 9](INSTALL.md#9-optional-hdmi-tv-or-monitor-with-wrong-colours). |
| The internal panel drops to 720p when a TV is connected | Mirroring uses the TV's resolution. Turn it off in System Settings → Displays. |

## Input

| Symptom | What to try |
|---|---|
| The touchpad does not move | `kmutil showloaded --list-only \| grep -i voodoo` must list `VoodooI2C`. If only `VoodooGPIO` and `VoodooI2CServices` load, the VoodooI2C build does not match the Alder Lake I2C controller. |
| The internal keyboard does not type, a USB one works | Watch `ioreg -c IOHIDSystem -d 4 \| grep HIDIdleTime` while typing. If it never resets, the keyboard gets no interrupts: check that the HPET/IRQ patches are off. |
| `'"` and `\|` swapped with the ABNT2 layout | `Use ISO layout keyboard` must be `true` in VoodooPS2Keyboard (`build-efi.py` sets it). |
| Fn+F6/F7 do not change brightness | Known limitation; use Control Center. See [NOTES.md](NOTES.md#brightness). |

## Audio and Bluetooth

| Symptom | What to try |
|---|---|
| No audio device at all | `ls -la /Library/Audio/Plug-Ins/HAL/` must show `drwxr-xr-x` for `CS8409Speakers.driver`. If not, run `sudo chmod -R go+rX` on it and `sudo killall coreaudiod`. |
| No sound through headphones | The headphone jack is not supported by CS8409Audio. |
| No Bluetooth controller | Run `scripts/build-bluetooth.sh` and rebuild the EFI. `kmutil showloaded --list-only \| grep -i -E "realtek\|bluetoolfixup"` must list both kexts. |

## After a macOS update

Check the WhateverXe and WhateverXe-Graphics release notes. The graphics package may need to be
reinstalled after an update.
