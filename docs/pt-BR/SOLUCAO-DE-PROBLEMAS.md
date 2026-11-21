# Solução de problemas

[English](../TROUBLESHOOTING.md) · **Português**

Mude uma coisa por vez e monte a EFI de novo (`rm -rf build && python3 scripts/build-efi.py`).
Use `VERBOSE_BOOT=1` enquanto investiga: as últimas linhas da tela mostram onde o boot para.

Os itens marcados com † não aconteceram no notebook testado. São sugestões tiradas das
configurações de referência e da documentação do WhateverXe.

## Boot

| Sintoma | O que tentar |
|---|---|
| O menu do OpenCore só mostra outro disco, sem instalador nem recuperação | Aperte Espaço para mostrar as entradas escondidas. Esta EFI usa `HideAuxiliary=false`. |
| Trava em `[EB\|#LOG:EXITBS:START]` † | Quirks do Booter ou mapa de memória. Compare a sua BIOS com o [guia](INSTALACAO.md#3-ajustes-da-bios). |
| Tela preta depois do log verboso, mas o notebook continua ligado † | Adicione `-wex-edp-keep` aos boot-args (usado pela EFI do IdeaPad 3 e pela referência do Sequoia). |
| Kernel panic citando `AMFI`, `IO80211` ou `Skywalk` † | Desligue as quatro entradas de Wi-Fi e o bloqueio do Skywalk, instale com cabo ou ancoragem e religue depois. |
| Kernel panic citando `WhateverXe` † | Remova o `-igfxdvmt` e as `DeviceProperties` do iGPU. |

## Vídeo e monitores

| Sintoma | O que tentar |
|---|---|
| 7 MB de VRAM, fundo de tela branco, animações lentas | Instale o pacote WhateverXe-Graphics e reinicie. Confira se `ioreg -r -c AMFIAnchor -l` mostra `InstallStatus = 1`. |
| A tela apagou | O brilho foi a 0: a luz de fundo desligou, mas o painel não. Aumente pela Central de Controle (Cmd+Espaço, digite "Monitores"). |
| Monitor HDMI com tom rosado ou faixas de cor | Override de EDID: [guia, passo 9](INSTALACAO.md#9-opcional-tv-ou-monitor-hdmi-com-cores-erradas). |
| A tela interna cai para 720p ao ligar uma TV | O espelhamento usa a resolução da TV. Desligue-o em Ajustes do Sistema → Monitores. |

## Teclado e touchpad

| Sintoma | O que tentar |
|---|---|
| O touchpad não mexe | `kmutil showloaded --list-only \| grep -i voodoo` precisa listar o `VoodooI2C`. Se só carregarem `VoodooGPIO` e `VoodooI2CServices`, o build do VoodooI2C não reconhece o controlador I2C do Alder Lake. |
| O teclado interno não digita, um USB funciona | Acompanhe `ioreg -c IOHIDSystem -d 4 \| grep HIDIdleTime` enquanto digita. Se nunca zerar, o teclado não recebe interrupções: confira se os patches de HPET/IRQ estão desligados. |
| `'"` e `\|` trocadas no layout ABNT2 | O `Use ISO layout keyboard` precisa estar `true` no VoodooPS2Keyboard (o `build-efi.py` já faz isso). |
| Fn+F6/F7 não mudam o brilho | Limitação conhecida; use a Central de Controle. Veja as [notas](NOTAS.md#brilho). |

## Áudio e Bluetooth

| Sintoma | O que tentar |
|---|---|
| Nenhum dispositivo de áudio | `ls -la /Library/Audio/Plug-Ins/HAL/` precisa mostrar `drwxr-xr-x` no `CS8409Speakers.driver`. Se não mostrar, rode `sudo chmod -R go+rX` nele e `sudo killall coreaudiod`. |
| Sem som no fone com fio | A entrada de fone não é suportada pelo CS8409Audio. |
| Sem controlador Bluetooth | Rode o `scripts/build-bluetooth.sh` e monte a EFI de novo. `kmutil showloaded --list-only \| grep -i -E "realtek\|bluetoolfixup"` precisa listar os dois kexts. |

## Depois de atualizar o macOS

Veja as notas de versão do WhateverXe e do WhateverXe-Graphics. Pode ser preciso reinstalar o
pacote de vídeo depois de uma atualização.
