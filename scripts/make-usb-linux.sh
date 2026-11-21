#!/usr/bin/env bash
# Turn a USB stick into an OpenCore + macOS Tahoe recovery installer, from Linux.
# ERASES THE STICK. Usage: sudo scripts/make-usb-linux.sh /dev/sdX
# On macOS, see docs/INSTALL.md for the diskutil equivalent.
set -euo pipefail
DEV="${1:?usage: sudo $0 /dev/sdX}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
[ -b "$DEV" ] || { echo "$DEV is not a block device"; exit 1; }
name="$(basename "$DEV")"
# Safety: removable USB disks only, never an internal NVMe/SATA disk.
[ "$(cat /sys/block/$name/removable)" = 1 ] || { echo "$DEV is not removable, aborting"; exit 1; }
[ "$(lsblk -dno TRAN "$DEV")" = usb ] || { echo "$DEV is not a USB disk, aborting"; exit 1; }
[ -d "$ROOT/build/EFI/OC" ] || { echo "missing build/EFI (run scripts/build-efi.py)"; exit 1; }
[ -f "$ROOT/downloads/recovery-tahoe/BaseSystem.dmg" ] || { echo "missing recovery (run scripts/fetch-components.sh --recovery)"; exit 1; }
for t in wipefs sfdisk partx mkfs.fat; do command -v $t >/dev/null || { echo "missing $t (util-linux / dosfstools)"; exit 1; }; done
lsblk -o NAME,SIZE,MODEL,TRAN,FSTYPE,LABEL "$DEV"
read -rp "Everything on $DEV ($(lsblk -dno MODEL "$DEV")) will be ERASED. Type ERASE to continue: " ok
[ "$ok" = ERASE ] || { echo "cancelled"; exit 1; }
umount "${DEV}"?* 2>/dev/null || true
wipefs -a "$DEV"
printf "label: gpt\n,,U\n" | sfdisk -q "$DEV"           # one EFI System partition
partx -u "$DEV" || true; udevadm settle; sleep 1
wipefs -a "${DEV}1"                                     # old exFAT/Ventoy signatures confuse mount
mkfs.fat -F32 -n OPENCORE "${DEV}1"
mnt="$(mktemp -d)"; mount -t vfat "${DEV}1" "$mnt"
cp -r "$ROOT/build/EFI" "$mnt/"
mkdir -p "$mnt/com.apple.recovery.boot"
cp "$ROOT/downloads/recovery-tahoe/"* "$mnt/com.apple.recovery.boot/"
mkdir -p "$mnt/post-install"                            # files needed inside macOS later
cp "$ROOT/downloads/whateverxe-gfx/"*.pkg "$mnt/post-install/"
cp -r "$ROOT/downloads/cs8409audio/CS8409Speakers.driver" "$mnt/post-install/"
sync; umount "$mnt"; rmdir "$mnt"
echo "USB installer ready. Boot it with F12 -> UEFI: $(lsblk -dno MODEL "$DEV")"
