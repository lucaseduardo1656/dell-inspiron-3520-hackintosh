# Installation guide

**English** · [Português](pt-BR/INSTALACAO.md)

This guide installs macOS Tahoe 26 on a Dell Inspiron 15 3520 with the i5-1235U. Other CPU
or GPU variants of the 3520 are not covered. For general OpenCore background, the
[Dortania guide](https://dortania.github.io/OpenCore-Install-Guide/) explains every concept used
here.

## 1. Requirements

- Dell Inspiron 15 3520 with i5-1235U and Iris Xe (`lspci` shows `8086:46a8`).
- A USB stick of 4 GB or more. It will be erased.
- At least 80 GB of free disk space for macOS (more if you plan to try macOS 27 later; see
  [NOTES.md](NOTES.md#macos-27)).
- Internet access during installation. The Wi-Fi driver is included, but keep a fallback:
  USB tethering from an Android phone, or a USB Ethernet adapter.
- A backup of everything on the laptop.

## 2. Build the EFI

On any Mac or Linux machine:

```bash
git clone https://github.com/lucaseduardo1656/dell-inspiron-3520-hackintosh
cd dell-inspiron-3520-hackintosh
scripts/fetch-components.sh --recovery
VERBOSE_BOOT=1 python3 scripts/build-efi.py
```

- `fetch-components.sh` downloads every component listed in `components.lock`, checks its
  SHA-256 and also downloads the macOS Tahoe recovery image from Apple's servers.
- `build-efi.py` writes `build/EFI`. On the first run it generates an SMBIOS identity
  (MacBookPro16,2) in `private/smbios.plist`. Keep that file: building again reuses it.
- `VERBOSE_BOOT=1` shows the boot log instead of the Apple logo. Keep it for the first install:
  if something hangs, the last lines on screen tell you where.
- Bluetooth stays off in this first EFI, because its kext can only be built on macOS. Step 7
  turns it on.

To check the result with OpenCore's own validator:

```bash
downloads/opencore/Utilities/ocvalidate/ocvalidate build/EFI/OC/config.plist        # macOS
downloads/opencore/Utilities/ocvalidate/ocvalidate.linux build/EFI/OC/config.plist  # Linux
```

## 3. BIOS settings

Press F2 at power-on. Write down your current settings before you change anything.

| Setting | Value |
|---|---|
| Secure Boot | Disabled |
| Storage (SATA/NVMe) operation | AHCI |

Tested with BIOS 1.30.0. F12 at power-on opens the one-time boot menu.

## 4. Write the USB installer

**From Linux** (needs `util-linux` and `dosfstools`):

```bash
lsblk -o NAME,SIZE,MODEL,TRAN    # find the stick: TRAN = usb
sudo scripts/make-usb-linux.sh /dev/sdX
```

The script refuses non-removable and non-USB disks, and asks you to type `ERASE` before it
touches anything. Besides the EFI and the recovery image, it copies the two files you will need
inside macOS (the graphics package and the audio plugin) to a `post-install` folder on the stick.

**From macOS** (replace `diskN` with your stick, as shown by `diskutil list`):

```bash
diskutil eraseDisk FAT32 OPENCORE GPT /dev/diskN
cp -R build/EFI /Volumes/OPENCORE/
mkdir -p /Volumes/OPENCORE/com.apple.recovery.boot /Volumes/OPENCORE/post-install
cp downloads/recovery-tahoe/* /Volumes/OPENCORE/com.apple.recovery.boot/
cp downloads/whateverxe-gfx/*.pkg /Volumes/OPENCORE/post-install/
cp -R downloads/cs8409audio/CS8409Speakers.driver /Volumes/OPENCORE/post-install/
```

**From Windows:** see Dortania's
[USB guide](https://dortania.github.io/OpenCore-Install-Guide/installer-guide/), then copy
`build/EFI` and the recovery files as above.

## 5. Install macOS

1. Plug in the charger and the USB stick. Power on with **F12** and choose the stick
   (`UEFI: <stick name>`).
2. In the OpenCore menu, choose **macOS Base System**. With the verbose boot, white text scrolls
   for a few minutes; that is normal.
3. In Recovery, open **Disk Utility**, choose *View → Show All Devices*, and erase the target as
   **APFS**. Erase only the disk or partition you mean to use.
4. Quit Disk Utility and choose **Reinstall macOS Tahoe** on that volume.
5. The laptop restarts several times. Each time, boot from the stick with F12 and choose
   **macOS Installer** in OpenCore while it is listed, then the name of your volume.
6. In Setup Assistant you can skip the Apple Account and create a local user.

> [!NOTE]
> Setup Assistant can take a very long time on the automatic updates screen, because there is no
> graphics acceleration yet. In the tested install, a forced restart at that point was harmless.
> A white desktop background and slow animations are also expected until step 6.

## 6. Graphics acceleration

1. Open `post-install/WhateverXe-Graphics-0.4.4.pkg` from the stick. macOS blocks it the first
   time: go to **System Settings → Privacy & Security** and click **Open Anyway**.
2. Restart (F12 → stick → your volume).
3. Check **System Information → Graphics/Displays**: *Metal Support: Metal 2* and *VRAM 1536 MB*.

The AMFIAnchor status should be `InstallStatus = 1`:

```bash
ioreg -r -c AMFIAnchor -l | grep -E 'InstallStatus|LoadedAnchors'
```

## 7. Audio and Bluetooth

**Audio:** the kext is already in the EFI. The Core Audio plugin has to be installed in macOS:

```bash
sudo cp -R /Volumes/OPENCORE/post-install/CS8409Speakers.driver /Library/Audio/Plug-Ins/HAL/
sudo chown -R root:wheel /Library/Audio/Plug-Ins/HAL/CS8409Speakers.driver
sudo chmod -R go+rX /Library/Audio/Plug-Ins/HAL/CS8409Speakers.driver
sudo killall coreaudiod
```

The `chmod` is required: FAT32 does not keep Unix permissions, so the plugin arrives readable
only by root and Core Audio silently ignores it. *Internal Speakers* and *Internal Microphone*
should appear in **System Settings → Sound**. A stick written from Linux is an EFI partition, which
macOS does not mount on its own: find it with `diskutil list` and run `sudo diskutil mount diskNs1`.

**Bluetooth:** build the patched kext on the laptop, then build the EFI again:

```bash
xcode-select --install                 # Command Line Tools, if not installed yet
scripts/fetch-components.sh
scripts/build-bluetooth.sh
rm -rf build && python3 scripts/build-efi.py
```

Copy the new `build/EFI` to the stick and restart.

## 8. Boot without the USB stick

Once macOS boots reliably from the stick, copy OpenCore to the internal EFI partition:

```bash
rm -rf build && python3 scripts/build-efi.py        # without VERBOSE_BOOT: Apple logo at boot
sudo diskutil mount disk0s1                          # the internal EFI partition
ls /Volumes/EFI                                       # check what is already there first
cp -R build/EFI/OC /Volumes/EFI/EFI/
```

Then add a firmware boot entry for `\EFI\OC\OpenCore.efi`:

- **Tested:** from a Linux install on the same disk, with
  `sudo efibootmgr --create --disk /dev/nvme0n1 --part 1 --label OpenCore --loader '\EFI\OC\OpenCore.efi'`.
  `efibootmgr` puts the new entry first in the boot order.
- **Not tested here:** the Dell BIOS (F2) has a *Boot Sequence → Add Boot Option* screen that
  takes a file path. If the disk has no other operating system, copying `build/EFI/BOOT` as well
  makes the firmware's fallback loader start OpenCore.

macOS cannot create the entry itself: OpenCore's `RequestBootVarRouting` keeps macOS away from
the firmware boot order. Keep the USB stick as a recovery tool.

## 9. Optional: HDMI TV or monitor with wrong colours

If an HDMI display shows a pink cast or banding:

```bash
python3 scripts/edid-force-rgb.py build/edid-override
sudo mkdir -p /Library/Displays/Contents/Resources/Overrides
sudo cp -R build/edid-override/DisplayVendorID-* /Library/Displays/Contents/Resources/Overrides/
```

Restart. In **System Settings → Displays**, the display name gets an "(RGB)" suffix. To undo it,
delete that `DisplayVendorID-…` folder and restart. The reason is explained in
[NOTES.md](NOTES.md#hdmi-colours).

## Updating macOS

Minor Tahoe updates (26.x) are expected to work. Before you update, check the
[WhateverXe](https://github.com/b00t0x/WhateverXe/releases) and
[WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases) releases. The
graphics package may need to be reinstalled after an update.
