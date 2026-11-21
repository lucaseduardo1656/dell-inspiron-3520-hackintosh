#!/usr/bin/env python3
"""Build build/EFI (OpenCore 1.0.8) for macOS Tahoe on the Dell Inspiron 15 3520 (i5-1235U).

Inputs come from downloads/ (run scripts/fetch-components.sh first). The starting point is
the config template, ACPI tables and USB map published for the same laptop by
pedrovrs301-gif/dell-inspiron-3520-i5-1235u-sequoia, adapted for Tahoe. Every change to
that template is made below, in code, with the reason next to it. See docs/NOTES.md.

This script only writes to build/EFI. It never touches a disk.

The SMBIOS identity (serial, MLB, UUID, ROM) is generated once and kept in
private/smbios.plist. Keep it: changing it makes macOS see a different Mac
(iCloud, iMessage). Never publish it.
"""
import glob, os, plistlib, shutil, subprocess, sys, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(ROOT, "downloads")
OC = os.path.join(DL, "opencore")
TPL = os.path.join(DL, "ref-inspiron3520/template/GitHub-Dell-Inspiron-3520/EFI/OC")
IDEAPAD_PNLF = os.path.join(DL, "ref-ideapad3/EFI/OC/ACPI/SSDT-PNLF.aml")
OUT = os.path.join(ROOT, "build/EFI")
PRIVATE = os.path.join(ROOT, "private")


def kext(component, name):
    """Find <name> inside downloads/<component>, skipping kexts nested in other kexts."""
    hits = [p for p in glob.glob(os.path.join(DL, component, "**", name), recursive=True)
            if ".kext/" not in os.path.relpath(p, os.path.join(DL, component))]
    if not hits:
        sys.exit(f"missing {name} in downloads/{component} (run scripts/fetch-components.sh)")
    return sorted(hits, key=len)[0]


BT_KEXT = os.path.join(DL, "realtek-bt-src/build/RealtekBluetoothFirmware.kext")
HAVE_BT = os.path.isdir(BT_KEXT)

KEXTS = {
    "Lilu.kext": kext("lilu", "Lilu.kext"),
    "AMFIAnchor.kext": kext("amfianchor", "AMFIAnchor.kext"),
    "AMFIAnchorInjector.kext": os.path.join(DL, "amfianchor-src/Injectors/AMFIAnchorInjector.kext"),
    "AMFIPass.kext": os.path.join(DL, "rtl88wifi/Kexts/AMFIPass.kext"),
    "VirtualSMC.kext": kext("virtualsmc", "VirtualSMC.kext"),
    "SMCBatteryManager.kext": kext("virtualsmc", "SMCBatteryManager.kext"),
    "SMCProcessor.kext": kext("virtualsmc", "SMCProcessor.kext"),
    "IOSkywalkFamily.kext": os.path.join(DL, "rtl88wifi/Kexts/IOSkywalkFamily.kext"),
    "IO80211FamilyLegacy.kext": os.path.join(DL, "rtl88wifi/Kexts/IO80211FamilyLegacy.kext"),
    "RTL88WiFi.kext": os.path.join(DL, "rtl88wifi/Kexts/RTL88WiFi.kext"),
    "WhateverXe.kext": kext("whateverxe", "WhateverXe.kext"),
    "CpuTopologyRebuild.kext": kext("cputopologyrebuild", "CpuTopologyRebuild.kext"),
    "NVMeFix.kext": kext("nvmefix", "NVMeFix.kext"),
    "RestrictEvents.kext": kext("restrictevents", "RestrictEvents.kext"),
    "ECEnabler.kext": kext("ecenabler", "ECEnabler.kext"),
    # VoodooI2C 2.9.1 (latest release) does not match the Alder Lake I2C controller (8086:51e8).
    # The master build from Dortania (commit 927797d) does.
    "VoodooI2C.kext": kext("voodooi2c", "VoodooI2C.kext"),
    "VoodooI2CHID.kext": kext("voodooi2c", "VoodooI2CHID.kext"),
    "VoodooPS2Controller.kext": kext("voodoops2", "VoodooPS2Controller.kext"),
    "USBToolBox.kext": kext("usbtoolbox", "USBToolBox.kext"),
    "UTBMap.kext": os.path.join(TPL, "Kexts/UTBMap.kext"),
    "BrightnessKeys.kext": kext("brightnesskeys", "BrightnessKeys.kext"),
    "CS8409Audio.kext": kext("cs8409audio", "CS8409Audio.kext"),
    "BlueToolFixup.kext": kext("brcmpatchram", "BlueToolFixup.kext"),
}
if HAVE_BT:
    KEXTS["RealtekBluetoothFirmware.kext"] = BT_KEXT


def entry(bundle, exe=None, minK="", maxK="", enabled=True, comment=""):
    name = bundle.split("/")[-1][:-5]
    return {"Arch": "x86_64", "BundlePath": bundle, "Comment": comment, "Enabled": enabled,
            "ExecutablePath": f"Contents/MacOS/{name}" if exe is None else exe,
            "MaxKernel": maxK, "MinKernel": minK, "PlistPath": "Contents/Info.plist"}


# Load order matters (Lilu, AMFI, IO80211 and VoodooI2C dependencies).
KERNEL_ADD = [
    entry("Lilu.kext"),
    entry("AMFIAnchor.kext", minK="20.0.0", maxK="25.99.99", comment="required by WhateverXe-Graphics"),
    entry("AMFIAnchorInjector.kext", exe="", minK="20.0.0", maxK="25.99.99", comment="anchor for the WhateverXe-Graphics CA"),
    entry("AMFIPass.kext", minK="23.0.0", comment="legacy Wi-Fi stack; on Tahoe needs -amfipassbeta"),
    entry("VirtualSMC.kext"),
    entry("SMCBatteryManager.kext"),
    entry("SMCProcessor.kext"),
    entry("IOSkywalkFamily.kext", minK="23.0.0", comment="RTL88WiFi"),
    entry("IO80211FamilyLegacy.kext", minK="23.0.0", comment="RTL88WiFi (without the AirPortBrcmNIC plugin)"),
    entry("RTL88WiFi.kext", minK="23.0.0", comment="Wi-Fi RTL8821CE"),
    entry("WhateverXe.kext", comment="Iris Xe 46A8"),
    entry("CpuTopologyRebuild.kext"),
    entry("NVMeFix.kext"),
    entry("RestrictEvents.kext"),
    entry("ECEnabler.kext"),
    entry("VoodooI2C.kext/Contents/PlugIns/VoodooInput.kext"),
    entry("VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext"),
    entry("VoodooI2C.kext/Contents/PlugIns/VoodooI2CServices.kext"),
    entry("VoodooI2C.kext"),
    entry("VoodooI2CHID.kext", comment="Goodix touchpad 27C6:0D43"),
    entry("VoodooPS2Controller.kext"),
    entry("VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Keyboard.kext"),
    entry("VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Mouse.kext", enabled=False),
    entry("VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Trackpad.kext", enabled=False),
    entry("USBToolBox.kext"),
    entry("UTBMap.kext", exe="", comment="Inspiron 3520 USB map (reference repository)"),
    entry("BrightnessKeys.kext", comment="brightness keys"),
    entry("CS8409Audio.kext", minK="25.0.0", comment="speakers + microphone; needs CS8409Speakers.driver in macOS"),
    entry("RealtekBluetoothFirmware.kext", minK="21.0.0", enabled=HAVE_BT,
          comment="Bluetooth 0bda:c829 (v1.0.2 + Dell patch, scripts/build-bluetooth.sh)"),
    entry("BlueToolFixup.kext", minK="21.0.0", enabled=HAVE_BT, comment="third-party Bluetooth; needs -btlfxboardid"),
]

BOOT_ARGS = ("-vi2c-force-polling -allow3d -disablegfxfirmware -igfxdvmt -amfipassbeta"
             + (" -btlfxboardid" if HAVE_BT else ""))
if os.environ.get("VERBOSE_BOOT") == "1":  # verbose boot for the first install / debugging
    BOOT_ARGS = "-v keepsyms=1 debug=0x100 " + BOOT_ARGS


def smbios():
    path = os.path.join(PRIVATE, "smbios.plist")
    if os.path.exists(path):
        return plistlib.load(open(path, "rb"))
    os.makedirs(PRIVATE, exist_ok=True)
    tool = os.path.join(OC, "Utilities/macserial/macserial" + (".linux" if sys.platform.startswith("linux") else ""))
    os.chmod(tool, 0o755)
    line = subprocess.run([tool, "-m", "MacBookPro16,2", "-n", "1"], capture_output=True, text=True, check=True).stdout
    serial, mlb = [x.strip() for x in line.strip().split("|")]
    # ROM: the Wi-Fi MAC address on Linux; random elsewhere (fine for booting).
    mac = None
    for iface in glob.glob("/sys/class/net/*/wireless"):
        mac = open(os.path.join(os.path.dirname(iface), "address")).read().strip()
    rom = bytes.fromhex(mac.replace(":", "")) if mac else os.urandom(6)
    data = {"SystemProductName": "MacBookPro16,2", "SystemSerialNumber": serial, "MLB": mlb,
            "SystemUUID": str(uuid.uuid4()).upper(), "ROM": rom}
    plistlib.dump(data, open(path, "wb"))
    os.chmod(path, 0o600)
    print("Generated a new SMBIOS identity in", path)
    return data


def main():
    if os.path.exists(OUT):
        sys.exit(f"{OUT} already exists; remove or rename it first.")
    for p in (TPL, IDEAPAD_PNLF):
        if not os.path.exists(p):
            sys.exit(f"missing {p} (run scripts/fetch-components.sh)")

    # OpenCore skeleton
    shutil.copytree(os.path.join(OC, "X64/EFI/BOOT"), os.path.join(OUT, "BOOT"))
    ocsrc, ocdst = os.path.join(OC, "X64/EFI/OC"), os.path.join(OUT, "OC")
    os.makedirs(ocdst)
    shutil.copy2(os.path.join(ocsrc, "OpenCore.efi"), ocdst)
    shutil.copytree(os.path.join(ocsrc, "Resources"), os.path.join(ocdst, "Resources"))
    os.makedirs(os.path.join(ocdst, "Drivers"))
    os.makedirs(os.path.join(ocdst, "Tools"))
    for d in ("OpenRuntime.efi", "OpenHfsPlus.efi", "ResetNvramEntry.efi"):
        shutil.copy2(os.path.join(ocsrc, "Drivers", d), os.path.join(ocdst, "Drivers"))
    shutil.copy2(os.path.join(ocsrc, "Tools/OpenShell.efi"), os.path.join(ocdst, "Tools"))

    shutil.copytree(os.path.join(TPL, "ACPI"), os.path.join(ocdst, "ACPI"))
    # The template's SSDT-PNLF declares \PNLF at the ACPI root, which Tahoe does not publish
    # (no backlight control). The IdeaPad 3 one declares \_SB.PC00.GFX0.PNLF, the same iGPU
    # path as this Dell.
    shutil.copy2(IDEAPAD_PNLF, os.path.join(ocdst, "ACPI/SSDT-PNLF.aml"))

    os.makedirs(os.path.join(ocdst, "Kexts"))
    for name, src in KEXTS.items():
        shutil.copytree(src, os.path.join(ocdst, "Kexts", name), symlinks=True)
    # Never load the Broadcom plugin shipped inside IO80211FamilyLegacy.
    shutil.rmtree(os.path.join(ocdst, "Kexts/IO80211FamilyLegacy.kext/Contents/PlugIns/AirPortBrcmNIC.kext"),
                  ignore_errors=True)
    # ABNT2 is an ISO keyboard. Without this, macOS swaps the key under Esc with the one
    # next to left Shift.
    kbd = os.path.join(ocdst, "Kexts/VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Keyboard.kext/Contents/Info.plist")
    kp = plistlib.load(open(kbd, "rb"))
    kp["IOKitPersonalities"]["ApplePS2Keyboard"]["Platform Profile"]["Default"]["Use ISO layout keyboard"] = True
    plistlib.dump(kp, open(kbd, "wb"))

    cfg = plistlib.load(open(os.path.join(TPL, "config.example.plist"), "rb"))
    # The HPET/IRQ patches from the Sequoia template stop the PS/2 keyboard from receiving
    # interrupts on Tahoe (the keyboard driver attaches, but no key arrives).
    for p in cfg["ACPI"]["Patch"]:
        if p.get("Comment", "").startswith(("HPET ", "IPIC IRQ", "RTC IRQ", "TIMR IRQ")):
            p["Enabled"] = False
    for a in cfg["ACPI"]["Add"]:
        if a["Path"] == "SSDT-HPET.aml":
            a["Enabled"] = False
    cfg["Kernel"]["Add"] = KERNEL_ADD
    cfg["Kernel"]["Block"] = [{"Arch": "x86_64", "Comment": "RTL88WiFi: use the legacy Skywalk",
                               "Enabled": True, "Identifier": "com.apple.iokit.IOSkywalkFamily",
                               "MaxKernel": "", "MinKernel": "23.0.0", "Strategy": "Exclude"}]
    # DVMT pre-allocation is fixed at 60 MB on this Dell.
    cfg["DeviceProperties"]["Add"] = {"PciRoot(0x0)/Pci(0x2,0x0)": {
        "framebuffer-patch-enable": bytes.fromhex("01000000"),
        "framebuffer-stolenmem": bytes.fromhex("0000C003")}}
    nv = cfg["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
    nv["boot-args"] = BOOT_ARGS
    nv["csr-active-config"] = bytes.fromhex("03080000")
    nv["prev-lang:kbd"] = b"pt-BR:128"
    cfg["UEFI"]["Drivers"] = [
        {"Arguments": "", "Comment": d, "Enabled": True, "HideVerbose": False, "LoadEarly": False, "Path": d}
        for d in ("OpenRuntime.efi", "OpenHfsPlus.efi", "ResetNvramEntry.efi")]
    cfg["Misc"]["Tools"] = [{"Arguments": "", "Auxiliary": True, "Comment": "UEFI shell", "Enabled": True,
                             "Flavour": "OpenShell:UEFIShell:Shell", "FullNvramAccess": False,
                             "Name": "UEFI Shell", "Path": "OpenShell.efi", "RealPath": False,
                             "TextMode": False}]
    cfg["Misc"]["Security"]["ScanPolicy"] = 0          # see every disk, including the USB installer
    cfg["Misc"]["Security"]["SecureBootModel"] = "Disabled"
    cfg["Misc"]["Boot"]["Timeout"] = 10
    cfg["Misc"]["Boot"]["HideAuxiliary"] = False      # True hides the recovery/installer entry
    cfg["PlatformInfo"]["Generic"].update(smbios())
    plistlib.dump(cfg, open(os.path.join(ocdst, "config.plist"), "wb"))

    print("EFI built in", OUT)
    if not HAVE_BT:
        print("NOTE: Bluetooth is off. After installing macOS, run scripts/build-bluetooth.sh"
              " on the laptop and build the EFI again.")


if __name__ == "__main__":
    main()
