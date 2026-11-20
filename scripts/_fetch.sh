#!/usr/bin/env bash
# Shared download helper (sourced by the download scripts). A file is fetched to <dest>.part, checked, then renamed
# into place, so an interrupted transfer never leaves a file that a later run would mistake for a complete one.
# An existing file is reused only if it passes the same check.

valid_file() {   # valid_file <path> [<name whose extension gives the format>]
  # zip/xlsx -> archive test; xls -> OLE2 signature; pdf -> header and EOF marker; anything else -> non-empty
  local f="$1" kind="${2:-$1}"
  [ -s "$f" ] || return 1
  case "$kind" in
    *.zip|*.xlsx) unzip -tq "$f" >/dev/null 2>&1 ;;
    *.xls) [ "$(head -c 8 "$f" | od -An -tx1 | tr -d ' \n')" = "d0cf11e0a1b11ae1" ] ;;
    *.pdf) head -c 5 "$f" | grep -q '%PDF' && tail -c 2048 "$f" | grep -q '%%EOF' ;;
    *) return 0 ;;
  esac
}

fetch() {        # fetch <url> <dest> [extra curl args...]
  local url="$1" dest="$2"; shift 2
  mkdir -p "$(dirname "$dest")"
  if valid_file "$dest"; then return 0; fi
  if [ -e "$dest" ]; then echo "existing $dest failed its integrity check; downloading again" >&2; fi
  curl -fL --retry 3 "$@" -o "$dest.part" "$url"
  if ! valid_file "$dest.part" "$dest"; then
    echo "integrity check failed for $url" >&2
    return 1
  fi
  mv -f "$dest.part" "$dest"
}
