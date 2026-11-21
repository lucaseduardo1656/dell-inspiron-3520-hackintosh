# Guia de instalação

[English](../INSTALL.md) · **Português**

Este guia instala o macOS Tahoe 26 num Dell Inspiron 15 3520 com i5-1235U. Outras variantes de
CPU ou GPU do 3520 não estão cobertas. Para os conceitos do OpenCore, o
[guia da Dortania](https://dortania.github.io/OpenCore-Install-Guide/) explica cada um que
aparece aqui.

## 1. Requisitos

- Dell Inspiron 15 3520 com i5-1235U e Iris Xe (o `lspci` mostra `8086:46a8`).
- Um pendrive de 4 GB ou mais. Ele será apagado.
- Pelo menos 80 GB livres no disco para o macOS (mais, se pretende testar o macOS 27 depois; veja
  as [notas](NOTAS.md#macos-27)).
- Internet durante a instalação. O driver de Wi-Fi está incluído, mas tenha um plano B:
  ancoragem USB de um celular Android ou um adaptador USB-Ethernet.
- Backup de tudo o que está no notebook.

## 2. Montar a EFI

Em qualquer Mac ou Linux:

```bash
git clone https://github.com/lucaseduardo1656/dell-inspiron-3520-hackintosh
cd dell-inspiron-3520-hackintosh
scripts/fetch-components.sh --recovery
VERBOSE_BOOT=1 python3 scripts/build-efi.py
```

- O `fetch-components.sh` baixa cada componente listado no `components.lock`, confere o SHA-256
  e baixa também a recuperação do macOS Tahoe dos servidores da Apple.
- O `build-efi.py` grava a `build/EFI`. Na primeira vez, ele gera uma identidade SMBIOS
  (MacBookPro16,2) em `private/smbios.plist`. Guarde esse arquivo: as próximas montagens reusam
  essa identidade.
- `VERBOSE_BOOT=1` mostra o log de boot em vez do logo da Apple. Use na primeira instalação: se
  algo travar, as últimas linhas da tela dizem onde.
- O Bluetooth fica desligado nessa primeira EFI, porque o kext dele só compila no macOS. O
  passo 7 liga o Bluetooth.

Para conferir o resultado com o validador do próprio OpenCore:

```bash
downloads/opencore/Utilities/ocvalidate/ocvalidate build/EFI/OC/config.plist        # macOS
downloads/opencore/Utilities/ocvalidate/ocvalidate.linux build/EFI/OC/config.plist  # Linux
```

## 3. Ajustes da BIOS

Aperte F2 ao ligar. Anote a configuração atual antes de mudar qualquer coisa.

| Opção | Valor |
|---|---|
| Secure Boot | Disabled |
| Modo do armazenamento (SATA/NVMe) | AHCI |

Testado com a BIOS 1.30.0. O F12 ao ligar abre o menu de boot.

## 4. Gravar o pendrive

**No Linux** (precisa de `util-linux` e `dosfstools`):

```bash
lsblk -o NAME,SIZE,MODEL,TRAN    # ache o pendrive: TRAN = usb
sudo scripts/make-usb-linux.sh /dev/sdX
```

O script recusa discos que não sejam USB removíveis e pede que você digite `ERASE` antes de
mexer em qualquer coisa. Além da EFI e da recuperação, ele copia para uma pasta `post-install`
no pendrive os dois arquivos que você vai precisar dentro do macOS: o pacote de vídeo e o plugin
de áudio.

**No macOS** (troque `diskN` pelo pendrive, como aparece no `diskutil list`):

```bash
diskutil eraseDisk FAT32 OPENCORE GPT /dev/diskN
cp -R build/EFI /Volumes/OPENCORE/
mkdir -p /Volumes/OPENCORE/com.apple.recovery.boot /Volumes/OPENCORE/post-install
cp downloads/recovery-tahoe/* /Volumes/OPENCORE/com.apple.recovery.boot/
cp downloads/whateverxe-gfx/*.pkg /Volumes/OPENCORE/post-install/
cp -R downloads/cs8409audio/CS8409Speakers.driver /Volumes/OPENCORE/post-install/
```

**No Windows:** veja o
[guia de pendrive da Dortania](https://dortania.github.io/OpenCore-Install-Guide/installer-guide/)
e depois copie a `build/EFI` e os arquivos de recuperação como acima.

## 5. Instalar o macOS

1. Conecte o carregador e o pendrive. Ligue apertando **F12** e escolha o pendrive
   (`UEFI: <nome do pendrive>`).
2. No menu do OpenCore, escolha **macOS Base System**. Com o boot verboso, texto branco rola por
   alguns minutos; é normal.
3. Na recuperação, abra o **Utilitário de Disco**, escolha *Visualizar → Mostrar Todos os
   Dispositivos* e apague o destino como **APFS**. Apague só o disco ou a partição que você
   pretende usar.
4. Feche o Utilitário de Disco e escolha **Reinstalar macOS Tahoe** nesse volume.
5. O notebook reinicia várias vezes. Em cada uma, aperte F12, escolha o pendrive e, no OpenCore,
   escolha **macOS Installer** enquanto ele aparecer; depois, o nome do seu volume.
6. No Assistente de Configuração, dá para pular a Conta Apple e criar um usuário local.

> [!NOTE]
> O Assistente de Configuração pode demorar muito na tela de atualizações automáticas, porque
> ainda não há aceleração de vídeo. Na instalação testada, forçar o reinício nesse ponto não
> causou problema. O fundo de tela branco e as animações lentas também são esperados até o passo 6.

## 6. Aceleração de vídeo

1. Abra o `post-install/WhateverXe-Graphics-0.4.4.pkg` do pendrive. O macOS bloqueia na primeira
   vez: vá em **Ajustes do Sistema → Privacidade e Segurança** e clique em **Abrir Mesmo Assim**.
2. Reinicie (F12 → pendrive → seu volume).
3. Confira em **Informações do Sistema → Gráficos/Monitores**: *Suporte a Metal: Metal 2* e
   *VRAM 1536 MB*.

O AMFIAnchor deve estar com `InstallStatus = 1`:

```bash
ioreg -r -c AMFIAnchor -l | grep -E 'InstallStatus|LoadedAnchors'
```

## 7. Áudio e Bluetooth

**Áudio:** o kext já está na EFI. O plugin do Core Audio precisa ser instalado no macOS:

```bash
sudo cp -R /Volumes/OPENCORE/post-install/CS8409Speakers.driver /Library/Audio/Plug-Ins/HAL/
sudo chown -R root:wheel /Library/Audio/Plug-Ins/HAL/CS8409Speakers.driver
sudo chmod -R go+rX /Library/Audio/Plug-Ins/HAL/CS8409Speakers.driver
sudo killall coreaudiod
```

O `chmod` é obrigatório: o FAT32 não guarda permissões Unix, então o plugin chega legível só
para o root e o Core Audio o ignora sem avisar. *Alto-falantes Internos* e *Microfone Interno*
devem aparecer em **Ajustes do Sistema → Som**. Um pendrive gravado no Linux é uma partição EFI,
que o macOS não monta sozinho: ache-a com `diskutil list` e rode `sudo diskutil mount diskNs1`.

**Bluetooth:** compile o kext com o patch no próprio notebook e monte a EFI de novo:

```bash
xcode-select --install                 # Command Line Tools, se ainda não estiverem instaladas
scripts/fetch-components.sh
scripts/build-bluetooth.sh
rm -rf build && python3 scripts/build-efi.py
```

Copie a `build/EFI` nova para o pendrive e reinicie.

## 8. Ligar sem o pendrive

Quando o macOS estiver ligando de forma estável pelo pendrive, copie o OpenCore para a partição
EFI interna:

```bash
rm -rf build && python3 scripts/build-efi.py        # sem VERBOSE_BOOT: logo da Apple no boot
sudo diskutil mount disk0s1                          # a partição EFI interna
ls /Volumes/EFI                                       # veja antes o que já existe nela
cp -R build/EFI/OC /Volumes/EFI/EFI/
```

Depois, crie uma entrada no firmware para `\EFI\OC\OpenCore.efi`:

- **Testado:** a partir de um Linux instalado no mesmo disco, com
  `sudo efibootmgr --create --disk /dev/nvme0n1 --part 1 --label OpenCore --loader '\EFI\OC\OpenCore.efi'`.
  O `efibootmgr` coloca a entrada nova em primeiro na ordem de boot.
- **Não testado aqui:** a BIOS da Dell (F2) tem uma tela *Boot Sequence → Add Boot Option* que
  aceita um caminho de arquivo. Se o disco não tiver outro sistema, copiar também a
  `build/EFI/BOOT` faz o carregador padrão do firmware iniciar o OpenCore.

O macOS não consegue criar essa entrada: o `RequestBootVarRouting` do OpenCore impede o macOS de
mexer na ordem de boot do firmware. Guarde o pendrive como ferramenta de resgate.

## 9. Opcional: TV ou monitor HDMI com cores erradas

Se um monitor HDMI mostrar tom rosado ou faixas de cor:

```bash
python3 scripts/edid-force-rgb.py build/edid-override
sudo mkdir -p /Library/Displays/Contents/Resources/Overrides
sudo cp -R build/edid-override/DisplayVendorID-* /Library/Displays/Contents/Resources/Overrides/
```

Reinicie. Em **Ajustes do Sistema → Monitores**, o nome do monitor ganha "(RGB)". Para desfazer,
apague essa pasta `DisplayVendorID-…` e reinicie. O motivo está nas
[notas](NOTAS.md#cores-no-hdmi).

## Atualizar o macOS

Atualizações menores do Tahoe (26.x) devem funcionar. Antes de atualizar, veja as releases do
[WhateverXe](https://github.com/b00t0x/WhateverXe/releases) e do
[WhateverXe-Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases). Pode ser preciso
reinstalar o pacote de vídeo depois de uma atualização.
