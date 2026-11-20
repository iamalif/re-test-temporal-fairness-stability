#!/usr/bin/env bash
# Append-only log of raw-file hashes (QA 3, R3-2): an entry already in logs/raw_sha256.txt must still match the file
# on disk (otherwise exit 1); files not yet logged are appended. The log is never rewritten.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
touch logs/raw_sha256.txt
new=$(mktemp)
find data/raw -type f ! -name '_files.txt' ! -name '*.part' -print0 | sort -z | xargs -0 shasum -a 256 > "$new"
status=0
while read -r h f; do
  old=$(awk -v f="$f" '$2 == f {print $1}' logs/raw_sha256.txt | tail -1)
  if [ -z "$old" ]; then
    echo "$h  $f" >> logs/raw_sha256.txt
  elif [ "$old" != "$h" ]; then
    echo "raw file changed since it was logged: $f" >&2; status=1
  fi
done < "$new"
rm -f "$new"
echo "raw-hash log: $(wc -l < logs/raw_sha256.txt) entries"
exit $status
