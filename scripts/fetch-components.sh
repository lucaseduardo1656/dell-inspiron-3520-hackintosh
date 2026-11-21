#!/usr/bin/env bash
# Download every component listed in components.lock into downloads/ and verify it.
#
#   scripts/fetch-components.sh              kexts, OpenCore and reference repositories
#   scripts/fetch-components.sh --recovery   also the macOS Tahoe recovery image (~1 GB)
#
# Works on macOS and Linux. Needs: bash, curl, git, unzip, shasum or sha256sum, python3.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DL="$ROOT/downloads"
mkdir -p "$DL"

sha256() { if command -v shasum >/dev/null; then shasum -a 256 "$1"; else sha256sum "$1"; fi | cut -c1-64; }

fetch_zip() {  # dir url asset sha
  local dir="$DL/$1" url="$2" asset="$3" want="$4"
  if [ -f "$dir/.verified" ] && [ "$(cat "$dir/.verified")" = "$want" ]; then echo "ok   $1 (cached)"; return; fi
  rm -rf "$dir"; mkdir -p "$dir"
  curl -fsSL -o "$dir/$asset" "$url"
  local got; got="$(sha256 "$dir/$asset")"
  if [ "$got" != "$want" ]; then
    echo "FAIL $1: sha256 $got, expected $want" >&2; rm -rf "$dir"; exit 1
  fi
  case "$asset" in *.zip) unzip -q -o "$dir/$asset" -d "$dir";; esac
  echo "$want" > "$dir/.verified"
  echo "ok   $1"
}

fetch_git() {  # dir url commit
  local dir="$DL/$1" url="$2" commit="$3"
  if [ -d "$dir/.git" ] && [ "$(git -C "$dir" rev-parse HEAD)" = "$commit" ]; then echo "ok   $1 (cached)"; return; fi
  rm -rf "$dir"
  git init -q "$dir"
  git -C "$dir" fetch -q --depth 1 "$url" "$commit"
  git -C "$dir" -c advice.detachedHead=false checkout -q FETCH_HEAD
  echo "ok   $1 @ ${commit:0:7}"
}

while read -r kind a b c d e; do
  case "$kind" in
    release)  fetch_zip "$a" "https://github.com/$b/releases/download/$c/$d" "$d" "$e" ;;
    dortania) fetch_zip "$a" "https://github.com/dortania/build-repo/releases/download/$b/$c" "$c" "$d" ;;
    git)      fetch_git "$a" "$b" "$c" ;;
  esac
done < <(grep -v -E '^\s*(#|$)' "$ROOT/components.lock")

# The Inspiron 3520 reference repository ships its EFI template inside a zip.
REF="$DL/ref-inspiron3520"
if [ ! -d "$REF/template" ]; then
  unzip -q -o "$REF/Dell-Inspiron-3520-Guia-GitHub.zip" -d "$REF/template"
fi

if [ "${1:-}" = "--recovery" ]; then
  # Tahoe recovery from Apple's servers, via OpenCore's macrecovery (board ID from its recovery_urls.txt).
  out="$DL/recovery-tahoe"; mkdir -p "$out"
  if [ ! -f "$out/BaseSystem.dmg" ]; then
    python3 "$DL/opencore/Utilities/macrecovery/macrecovery.py" \
      -b Mac-CFF7D910A743CAAF -m 00000000000000000 -os latest -o "$out" download
  fi
  echo "ok   recovery-tahoe"
fi
echo "All components are in $DL"
