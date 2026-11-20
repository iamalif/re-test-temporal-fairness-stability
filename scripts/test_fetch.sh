#!/usr/bin/env bash
# Synthetic tests of the download integrity checks (QA 2, A5): corrupt files on the temporary .part path must be
# rejected, valid ones accepted. Writes results/validation/fetch_tests.json; exits non-zero on any failure.
set -uo pipefail
cd "$(dirname "$0")/.."
source scripts/_fetch.sh
T=$(mktemp -d)
fail=0; out="{"
check() {   # check <label> <expected: accept|reject> <path> <name>
  if valid_file "$3" "$4"; then got=accept; else got=reject; fi
  [ "$got" = "$2" ] || fail=1
  out="$out\"$1\": \"$got (expected $2)\","
}
echo "not an archive" > "$T/c.zip.part";  check corrupt_zip reject "$T/c.zip.part" c.zip
echo "not an archive" > "$T/c.xlsx.part"; check corrupt_xlsx reject "$T/c.xlsx.part" c.xlsx
echo "not a pdf" > "$T/c.pdf.part";       check corrupt_pdf reject "$T/c.pdf.part" c.pdf
printf '%%PDF-1.4 truncated' > "$T/t.pdf.part"; check truncated_pdf reject "$T/t.pdf.part" t.pdf
echo "junk" > "$T/c.xls.part";            check corrupt_xls reject "$T/c.xls.part" c.xls
: > "$T/e.csv.part";                      check empty_file reject "$T/e.csv.part" e.csv
python3 -c "import zipfile,sys;z=zipfile.ZipFile(sys.argv[1],'w');z.writestr('a.csv','x');z.close()" "$T/g.zip.part"
check valid_zip accept "$T/g.zip.part" g.zip
head -c 60 "$T/g.zip.part" > "$T/tr.zip.part"; check truncated_zip reject "$T/tr.zip.part" tr.zip
printf '%%PDF-1.4\nbody\n%%%%EOF\n' > "$T/g.pdf.part"; check valid_pdf accept "$T/g.pdf.part" g.pdf
printf '\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1rest' > "$T/g.xls.part"; check valid_xls accept "$T/g.xls.part" g.xls
mkdir -p results/validation
echo "${out%,}, \"all_passed\": $([ $fail -eq 0 ] && echo true || echo false)}" > results/validation/fetch_tests.json
cat results/validation/fetch_tests.json
rm -rf "$T"
exit $fail
