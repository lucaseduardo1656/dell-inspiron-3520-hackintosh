# Credits

**English** · [Português](README.pt-BR.md#créditos)

This repository has no binaries and copies no third-party files. `scripts/fetch-components.sh`
downloads each item below from its original source, at the version pinned in
[`components.lock`](components.lock). Each project keeps its own license. The licenses below were
read from each repository in November 2026; check the source before redistributing anything.

## The two reference builds

| Project | Author | What this repository uses from it | License |
|---|---|---|---|
| [dell-inspiron-3520-i5-1235u-sequoia](https://github.com/pedrovrs301-gif/dell-inspiron-3520-i5-1235u-sequoia) | pedrovrs301-gif | The starting point for this setup: config template (quirks, CPU emulation, NVRAM), ACPI tables, USB port map, the RealtekBluetoothFirmware patch for `0bda:c829`, and the research notes on this exact laptop on Sequoia | none stated; downloaded at build time, never copied here |
| [AlderLake-IrisXe-OpenCore](https://github.com/Aniket601/AlderLake-IrisXe-OpenCore) | Aniket601 | `SSDT-PNLF` under the iGPU (brightness), and the Lenovo IdeaPad 3 (i5-1235U) Tahoe configuration used to find the keyboard fix | BSD-3-Clause |

## Components

| Component | Author | Role | License |
|---|---|---|---|
| [OpenCorePkg](https://github.com/acidanthera/OpenCorePkg) | acidanthera | bootloader, `ocvalidate`, `macserial`, `macrecovery` | BSD-3-Clause |
| [Lilu](https://github.com/acidanthera/Lilu) | acidanthera | kernel patching framework | BSD-3-Clause |
| [VirtualSMC](https://github.com/acidanthera/VirtualSMC) | acidanthera | SMC emulation, battery, CPU sensors | BSD-3-Clause |
| [NVMeFix](https://github.com/acidanthera/NVMeFix) | acidanthera | NVMe power management | BSD-style (LICENSE.txt) |
| [RestrictEvents](https://github.com/acidanthera/RestrictEvents) | acidanthera | system event patches | BSD-3-Clause |
| [VoodooPS2](https://github.com/acidanthera/VoodooPS2) | acidanthera | PS/2 keyboard | APSL 2.0 |
| [BrcmPatchRAM](https://github.com/acidanthera/BrcmPatchRAM) | acidanthera | BlueToolFixup (third-party Bluetooth) | GPL-2.0 |
| [BrightnessKeys](https://github.com/acidanthera/BrightnessKeys) | acidanthera | brightness key handling (1.0.4 build) | BSD-3-Clause |
| [WhateverXe](https://github.com/b00t0x/WhateverXe) | b00t0x | Intel Xe-LP graphics support | BSD-3-Clause |
| [WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics) | b00t0x | graphics driver package installed in macOS | BSD-2-Clause for its tooling; payloads per its THIRD_PARTY.md |
| [AMFIAnchor](https://github.com/b00t0x/AMFIAnchor) | b00t0x | trusts the WhateverXe-Graphics signing certificate | BSD-3-Clause |
| [CpuTopologyRebuild](https://github.com/b00t0x/CpuTopologyRebuild) | b00t0x | hybrid P/E-core topology | BSD-3-Clause |
| [VoodooI2C](https://github.com/VoodooI2C/VoodooI2C) | VoodooI2C contributors | I2C touchpad (master build with Alder Lake support) | GPL-3.0 |
| [CS8409Audio](https://github.com/nwrafael/CS8409Audio) | nwrafael; `CS8409Speakers` forked from JulioNectar's XeSpeakers | speakers and microphone | GPL-2.0 (kext); TSNPL 1.0 (Core Audio plugin) |
| [RTL88WiFi](https://github.com/X1REN41L/RTL88WiFi) | X1REN41L | RTL8821CE Wi-Fi and the legacy Wi-Fi stack kexts | GPL-2.0 |
| [RealtekBluetoothFirmware](https://github.com/thegwchr/RealtekBluetoothFirmware) | thegwchr | Realtek Bluetooth firmware loader (built with the patch above) | GPL-2.0-or-later |
| [ECEnabler](https://github.com/1Revenger1/ECEnabler) | 1Revenger1 | embedded controller field access (battery) | no license file |
| [USBToolBox kext](https://github.com/USBToolBox/kext) | dhinakg and contributors | USB port map | no license file |
| [build-repo](https://github.com/dortania/build-repo) | Dortania | builds of VoodooI2C and BrightnessKeys master | — |

## Research and issue threads

These threads answered specific questions on this laptop:

- [WhateverXe #64](https://github.com/b00t0x/WhateverXe/issues/64): reports of the `46a8` GPU with
  Metal 2 (Aniket601 on Ventura, iqsanfm on Tahoe with a Latitude 7430), including the need for
  `-disablegfxfirmware`.
- [WhateverXe #74](https://github.com/b00t0x/WhateverXe/issues/74) (yuanyiHY) and
  [#120](https://github.com/b00t0x/WhateverXe/issues/120) (Aqpcet, wen089130): HDMI colour
  corruption caused by YCbCr and deep colour, and the EDID clean-up that fixes it.
- [WhateverXe #43](https://github.com/b00t0x/WhateverXe/issues/43): eDP link training on Alder Lake.
- [Dortania OpenCore guides](https://dortania.github.io/OpenCore-Install-Guide/): the reference
  for every OpenCore concept used here.

If your work is used here and is missing or credited wrongly, please open an issue.
