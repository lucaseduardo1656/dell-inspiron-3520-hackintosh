# Notas técnicas

[English](../NOTES.md) · **Português**

Como se chegou a esta configuração: o que falhou nos primeiros boots, como cada problema foi
diagnosticado e por que a correção é a que é. Sirva-se delas quando algo quebrar depois de uma
atualização, ou para adaptar esta configuração a outro notebook Alder Lake parecido.

## Ponto de partida

Nenhuma configuração pública tinha este notebook rodando o Tahoe com aceleração de vídeo. Três
fontes, juntas, indicavam que era possível:

| Fonte | O que mostrava |
|---|---|
| [pedrovrs301-gif/dell-inspiron-3520-i5-1235u-sequoia](https://github.com/pedrovrs301-gif/dell-inspiron-3520-i5-1235u-sequoia) | O mesmo notebook no Sequoia 15.8.3, com Metal 2, Wi-Fi e alto-falantes |
| [WhateverXe #64](https://github.com/b00t0x/WhateverXe/issues/64) | A mesma GPU (`46a8`) com Metal 2 no Tahoe 26.7.1, num Dell Latitude 7430 |
| [nwrafael/CS8409Audio](https://github.com/nwrafael/CS8409Audio) | Áudio testado num Inspiron 3520 com Tahoe 26.7.1 |

A EFI parte do template do Sequoia (tabelas ACPI, quirks, emulação de CPU, mapa USB) e muda o
que o Tahoe exige. Cada mudança é aplicada no [`scripts/build-efi.py`](../../scripts/build-efi.py),
ao lado de um comentário que a explica.

## Vídeo

O WhateverXe (kext na EFI) e o WhateverXe-Graphics (pacote instalado no macOS) adaptam os drivers
de Tiger Lake da Apple para GPUs Xe-LP. Os dois funcionam juntos:

- A release oficial 0.8.3 do WhateverXe funciona nesta máquina. A referência do Sequoia usava um
  build local, nunca publicado.
- O WhateverXe-Graphics 0.4.4 precisa do **AMFIAnchor** e do `AMFIAnchorInjector.kext`, que
  fazem o sistema confiar no certificado que assina os drivers dele.
- O `-disablegfxfirmware` é obrigatório. Sem ele, o acelerador nunca inicia.
- Este Dell tem o DVMT fixo em 60 MB, então a EFI define `framebuffer-stolenmem` e `-igfxdvmt`,
  como o README do WhateverXe descreve.

Antes de instalar o pacote, o macOS roda sem aceleração: 7 MB de VRAM, fundo de tela branco e
animações lentas.

## Touchpad: build do master do VoodooI2C

**Sintoma:** o touchpad não funcionava, e só dois plugins do VoodooI2C (`VoodooGPIO` e
`VoodooI2CServices`) carregavam.

**Causa:** o VoodooI2C 2.9.1, última release, só reconhece controladores I2C da Intel até a 10ª
geração. O controlador do Alder Lake (`8086:51e8`) não está na lista dele, então o kext principal
nunca se conecta. O master do projeto ganhou o `VoodooI2CPCIAlderLakeController`, com os valores
de temporização desse controlador, depois dessa release.

**Correção:** usar o build do master feito pela Dortania, commit `927797d`. O binário da 2.9.1
também não tem o código que lê esses valores de temporização, então editar o `Info.plist` dele
não bastaria.

## Teclado: patches de HPET e IRQ

**Sintoma:** o teclado interno não digitava, enquanto um teclado USB externo funcionava. O
`ApplePS2Keyboard` estava conectado e registrado como teclado.

**Diagnóstico:** o `HIDIdleTime` do `IOHIDSystem` zera com qualquer evento de entrada. Digitando
no teclado interno por um minuto, ele nunca zerou; com o teclado USB, zerou na hora. O driver
estava carregado e não recebia teclas, o que aponta para falta de interrupções.

```bash
ioreg -c IOHIDSystem -d 4 | grep HIDIdleTime
```

**Causa:** o template do Sequoia desativa o HPET e altera as IRQs de IPIC, RTC e TIMR (a
`SSDT-HPET` mais cinco patches no DSDT). O IdeaPad 3 (mesmo chipset), com o teclado funcionando
no Tahoe, não usa nenhum deles, e o Alder Lake não precisa deles.

**Correção:** desligar esses patches e a `SSDT-HPET`.

## Teclado: layout ABNT2

**Sintoma:** com o layout *Português do Brasil – ABNT2*, a tecla abaixo do Esc (`'"`) e a tecla
ao lado do Shift esquerdo (`\|`) saíam trocadas.

**Causa:** o macOS troca essas duas teclas em teclados ISO quando o driver anuncia um teclado ANSI.

**Correção:** `Use ISO layout keyboard = true` no `Info.plist` do VoodooPS2Keyboard.

## Brilho

**Sintoma:** não havia como mudar o brilho.

**Causa:** não existia o dispositivo `PNLF`. A `SSDT-PNLF` do template declara `\PNLF` na raiz do
ACPI, e o Tahoe não publica dispositivos declarados ali.

**Correção:** usar a `SSDT-PNLF` do IdeaPad 3, que declara `\_SB.PC00.GFX0.PNLF` (o caminho do
iGPU é o mesmo neste Dell), mais o BrightnessKeys 1.0.4 (build da Dortania `37bdf47`). O brilho
agora funciona pela Central de Controle. Brilho 0 desliga a luz de fundo por completo; o painel
continua ligado.

**Teclas (pendente):** o teclado manda F1–F12 por padrão (Fn+Esc alterna o Fn-lock). Os eventos
de teclado foram registrados com um `CGEventTap`:

| Teclas | O que chega ao macOS |
|---|---|
| Fn+F1 / F2 / F3 | mute, volume−, volume+ (eventos de sistema; não precisa de nada) |
| Fn+F10 (PrtScr) | F13, que dá para associar em *Teclado → Atalhos de Teclado → Capturas de Tela* |
| Fn+F6 / F7 (brilho) | nada: o EC manda o brilho como evento ACPI |

A correção certa é uma SSDT que encaminhe esse evento ACPI para `Notify(PS2K, 0x0405/0x0406)`,
que o VoodooPS2 já entende. Escrevê-la exige o DSDT deste notebook, por isso ainda está pendente.
Remapear F6/F7 para F14/F15 foi tentado e descartado, porque custaria as teclas F6/F7.

## Áudio

**Sintoma:** o kext `CS8409Audio` carregava, mas o macOS não listava nenhum dispositivo de áudio.

**Causa:** o `CS8409Speakers.driver` estava com permissão `drwx------`. Ele veio de um pendrive
FAT32, que não guarda permissões Unix, então os arquivos ficaram legíveis só para o root. O
`coreaudiod` roda como `_coreaudiod` e ignorou o plugin sem registrar nada visível.

**Correção:** `sudo chmod -R go+rX` no plugin e depois `sudo killall coreaudiod`. Alto-falantes e
microfone funcionam a 48 kHz. O driver não suporta a entrada de fone.

## Wi-Fi

O RTL88WiFi precisa da pilha de Wi-Fi antiga da Apple: `IOSkywalkFamily`, `IO80211FamilyLegacy` e
`AMFIPass` injetados, e o `IOSkywalkFamily` nativo bloqueado. No Tahoe, o AMFIPass também precisa
de `-amfipassbeta`. O RTL88WiFi lista o Tahoe como "precisa de relatos"; aqui funcionou. O
desenvolvimento parou na 1.0.1.

## Bluetooth

O RealtekBluetoothFirmware oficial não reconhece o `0bda:c829`. A referência do Sequoia publica um
patch para a v1.0.2, que adiciona o reconhecimento USB e se recupera de firmware que ficou
carregado entre reinícios, mas ele nunca tinha sido compilado. O
[`scripts/build-bluetooth.sh`](../../scripts/build-bluetooth.sh) aplica o patch e compila o kext
com `make`, só com as Command Line Tools.

O kext também precisa do BlueToolFixup, do `-btlfxboardid` e de três chaves de NVRAM que vêm do
template (o `bluetoothInternalControllerInfo` tem de ter **14** bytes zero). O resultado é um
controlador `THIRD_PARTY_DONGLE` (firmware v61592) e um fone pareado com A2DP, HFP e AVRCP. É o
primeiro pareamento confirmado neste chip: a referência do Sequoia só tinha testado a descoberta
de aparelhos BLE.

## Cores no HDMI

**Sintoma:** uma TV (PHILCO, EDID `4183:0003`) mostrava tom rosado. A resolução e a taxa de
atualização estavam certas (1080p60).

**Tentativa 1:** um override de EDID sem suporte a YCbCr (byte 3 da extensão CEA: `0xf2` →
`0xc2`). O macOS aplicou o override, porque a TV passou a se chamar "(RGB)", mas o rosado
continuou.

**Causa:** o WhateverXe segue o **deep color** que a TV declara no bloco de dados HDMI (30/36
bits, flags `0xb8`) em vez de usar RGB de 8 bits. O mesmo comportamento aparece nas issues
[#74](https://github.com/b00t0x/WhateverXe/issues/74) e
[#120](https://github.com/b00t0x/WhateverXe/issues/120) do WhateverXe. Os boot-args discutidos
lá (`-wex-force-rgb8`, `-wex-force-ext-8bpc`) só existem em forks, não na 0.8.3.

**Correção:** limpar também as flags de deep color (`0xb8` → `0x80`). O
[`scripts/edid-force-rgb.py`](../../scripts/edid-force-rgb.py) gera o override para qualquer
monitor HDMI conectado.

## Detalhes da primeira instalação

- O `HideAuxiliary=true` escondia a entrada de recuperação, e o OpenCore só listava o outro disco.
  A EFI agora usa `false`. Apertar Espaço no menu do OpenCore também mostra as entradas
  escondidas.
- Gravar o pendrive no Linux: o `parted` costuma não estar instalado, então o script usa o
  `sfdisk`. Além disso, uma assinatura exFAT que sobrou do Ventoy confundia o `mount`, por isso o
  script roda `wipefs` na partição nova.

## macOS 27

O macOS 27 não suporta Macs Intel. O [NullMoth Liberator](https://github.com/nullmoth/liberator)
instala o macOS 27 ao lado de um Tahoe já existente em PCs com OpenCore. A partir do Beta 4
(novembro de 2026), ele leva os drivers de vídeo integrado Intel do Tahoe para o 27. Não foi
testado neste notebook, e as notas da versão dizem que a tela de notebooks não foi testada e que
o Wi-Fi não funciona no 27. Se pretende testar, deixe uns 92 GB livres no container APFS.
