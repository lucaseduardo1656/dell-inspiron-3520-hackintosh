# Technical notes

**English** · [Português](pt-BR/NOTAS.md)

How this configuration was reached: what failed on the first boots, how each problem was
diagnosed, and why the fix is what it is. Use it when something breaks after an update, or to
adapt this setup to a similar Alder Lake laptop.

## Starting point

No public setup had this laptop running Tahoe with graphics acceleration. Three sources together
suggested it was possible:

| Source | What it showed |
|---|---|
| [pedrovrs301-gif/dell-inspiron-3520-i5-1235u-sequoia](https://github.com/pedrovrs301-gif/dell-inspiron-3520-i5-1235u-sequoia) | The same laptop on Sequoia 15.8.3 with Metal 2, Wi-Fi and speakers |
| [WhateverXe #64](https://github.com/b00t0x/WhateverXe/issues/64) | The same GPU (`46a8`) with Metal 2 on Tahoe 26.7.1, on a Dell Latitude 7430 |
| [nwrafael/CS8409Audio](https://github.com/nwrafael/CS8409Audio) | Audio tested on an Inspiron 3520 running Tahoe 26.7.1 |

The EFI starts from the Sequoia template (ACPI tables, quirks, CPU emulation, USB map) and
changes what Tahoe needs. Every change is applied in [`scripts/build-efi.py`](../scripts/build-efi.py),
next to a comment explaining it.

## Graphics

WhateverXe (kext in the EFI) and WhateverXe-Graphics (package installed in macOS) adapt Apple's
Tiger Lake drivers to Xe-LP GPUs. They are used together:

- The official WhateverXe 0.8.3 release works on this machine. The Sequoia reference used a
  local, unpublished build.
- WhateverXe-Graphics 0.4.4 needs **AMFIAnchor** and `AMFIAnchorInjector.kext`, which trust the
  certificate that signs its drivers.
- `-disablegfxfirmware` is required. Without it, the accelerator never starts.
- This Dell has DVMT pre-allocation fixed at 60 MB, so the EFI sets
  `framebuffer-stolenmem` and `-igfxdvmt`, as the WhateverXe README describes.

Before the package is installed, macOS runs without acceleration: 7 MB of VRAM, a white desktop
background and slow animations.

## Touchpad: VoodooI2C master build

**Symptom:** the touchpad did not work, and only two VoodooI2C plugins (`VoodooGPIO`,
`VoodooI2CServices`) were loaded.

**Cause:** VoodooI2C 2.9.1, the latest release, matches I2C controllers only up to 10th-gen
Intel. The Alder Lake controller (`8086:51e8`) is not on its list, so the main kext never
attaches. Upstream master added `VoodooI2CPCIAlderLakeController`, with timing values for this
controller, after that release.

**Fix:** use Dortania's build of master, commit `927797d`. Version 2.9.1's binary also lacks the
code that reads those timing values, so editing its `Info.plist` would not be enough.

## Keyboard: HPET and IRQ patches

**Symptom:** the internal keyboard did not type, while an external USB keyboard worked.
`ApplePS2Keyboard` was attached and registered as a keyboard.

**Diagnosis:** `HIDIdleTime` in `IOHIDSystem` resets on any input event. While typing on the
internal keyboard for a minute it never reset, but it reset at once with the USB keyboard. The
driver was loaded and received no keystrokes, which points to missing interrupts.

```bash
ioreg -c IOHIDSystem -d 4 | grep HIDIdleTime
```

**Cause:** the Sequoia template disables HPET and patches IPIC/RTC/TIMR IRQs (`SSDT-HPET` plus
five DSDT patches). The IdeaPad 3 (same chipset), whose keyboard works on Tahoe, uses none of
these, and Alder Lake does not need them.

**Fix:** disable those patches and `SSDT-HPET`.

## Keyboard: ABNT2 layout

**Symptom:** with the *Brazilian – ABNT2* layout, the key under Esc (`'"`) and the key next to
left Shift (`\|`) were swapped.

**Cause:** macOS swaps those two keys on ISO keyboards when the driver reports an ANSI keyboard.

**Fix:** set `Use ISO layout keyboard = true` in the VoodooPS2Keyboard `Info.plist`.

## Brightness

**Symptom:** brightness could not be changed at all.

**Cause:** there was no `PNLF` device. The template's `SSDT-PNLF` declares `\PNLF` at the ACPI
root, and Tahoe does not publish devices declared there.

**Fix:** use the IdeaPad 3 `SSDT-PNLF`, which declares `\_SB.PC00.GFX0.PNLF` (the iGPU path is
the same on this Dell), plus BrightnessKeys 1.0.4 (Dortania build `37bdf47`). Brightness now works
from Control Center. Brightness 0 turns the backlight off entirely; the panel itself stays on.

**Keys (still open):** the keyboard sends F1–F12 by default (Fn+Esc toggles Fn-lock). Key events
were recorded with a `CGEventTap`:

| Keys | What reaches macOS |
|---|---|
| Fn+F1 / F2 / F3 | mute, volume down, volume up (system events, no fix needed) |
| Fn+F10 (PrtScr) | F13, which can be assigned in *Keyboard → Keyboard Shortcuts → Screenshots* |
| Fn+F6 / F7 (brightness) | nothing: the EC sends brightness as an ACPI event |

The right fix is an SSDT that forwards that ACPI event to `Notify(PS2K, 0x0405/0x0406)`, which
VoodooPS2 already understands. Writing it requires this laptop's DSDT, so it is still pending.
Remapping F6/F7 to F14/F15 was tried and rejected, because it would have cost the F6/F7 keys.

## Audio

**Symptom:** the `CS8409Audio` kext was loaded, but macOS listed no audio device at all.

**Cause:** `CS8409Speakers.driver` had mode `drwx------`. It came from a FAT32 USB stick, which
does not store Unix permissions, so the files were readable only by root. `coreaudiod` runs as
`_coreaudiod` and skipped the plugin without logging anything visible.

**Fix:** `sudo chmod -R go+rX` on the plugin, then `sudo killall coreaudiod`. Speakers and the
microphone work at 48 kHz. The driver does not support the headphone jack.

## Wi-Fi

RTL88WiFi needs Apple's legacy Wi-Fi stack: `IOSkywalkFamily`, `IO80211FamilyLegacy` and
`AMFIPass` injected, and the native `IOSkywalkFamily` blocked. On Tahoe, AMFIPass also needs
`-amfipassbeta`. RTL88WiFi lists Tahoe as "needs reports"; it worked here. Upstream development
has stopped at 1.0.1.

## Bluetooth

The official RealtekBluetoothFirmware does not match `0bda:c829`. The Sequoia reference publishes
a patch for v1.0.2, which adds the USB match and recovers from firmware left loaded across
reboots, but it had never been compiled. [`scripts/build-bluetooth.sh`](../scripts/build-bluetooth.sh)
applies the patch and builds the kext with `make`, using only the Command Line Tools.

The kext also needs BlueToolFixup, `-btlfxboardid` and three NVRAM keys from the template
(`bluetoothInternalControllerInfo` must be **14** zero bytes). The result is a
`THIRD_PARTY_DONGLE` controller (firmware v61592) and a headset paired with A2DP, HFP and
AVRCP. This is the first confirmed pairing on this chip: the Sequoia reference had only tested
BLE discovery.

## HDMI colours

**Symptom:** a TV (PHILCO, EDID `4183:0003`) showed a pink cast. Its resolution and refresh rate
were correct (1080p60).

**Attempt 1:** an EDID override without YCbCr support (CEA byte 3: `0xf2` → `0xc2`). macOS
applied it, since the TV was renamed "(RGB)", but the pink cast remained.

**Cause:** WhateverXe follows the **deep colour** support that the TV declares in its HDMI
vendor-specific data block (30/36-bit, flags `0xb8`) instead of driving RGB 8 bpc. The same
behaviour is reported in [WhateverXe #74](https://github.com/b00t0x/WhateverXe/issues/74) and
[#120](https://github.com/b00t0x/WhateverXe/issues/120). The boot-args discussed there
(`-wex-force-rgb8`, `-wex-force-ext-8bpc`) exist only in forks, not in 0.8.3.

**Fix:** also clear the deep-colour flags (`0xb8` → `0x80`).
[`scripts/edid-force-rgb.py`](../scripts/edid-force-rgb.py) builds the override for any
connected HDMI display.

## First install details

- `HideAuxiliary=true` hid the recovery entry, so OpenCore listed only the other disk. The EFI
  now sets it to `false`. Pressing Space in the OpenCore menu also shows hidden entries.
- Building the USB stick from Linux: `parted` is often missing, so the script uses `sfdisk`. Also,
  a leftover exFAT signature from Ventoy confused `mount`, so the script runs `wipefs` on the new
  partition.

## macOS 27

macOS 27 does not support Intel Macs. [NullMoth Liberator](https://github.com/nullmoth/liberator)
installs macOS 27 next to an existing Tahoe on OpenCore PCs. As of Beta 4 (November 2026), it
carries Intel integrated-graphics drivers from Tahoe over to 27. It has not been tested on this
laptop, and its release notes list laptop panels as untested and Wi-Fi as unsupported on 27. If
you plan to try it, leave about 92 GB free in the APFS container.
