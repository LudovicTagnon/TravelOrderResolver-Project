#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="${ROOT}/docs/report_pdf_ready.md"
OUTPUT="${1:-${ROOT}/deliverables/report_final.pdf}"
BIB="${ROOT}/docs/references.bib"

mkdir -p "$(dirname "${OUTPUT}")"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc introuvable" >&2
  exit 1
fi

pandoc \
  "${INPUT}" \
  --from=gfm \
  --toc \
  --toc-depth=3 \
  --pdf-engine=xelatex \
  -V geometry:margin=2.5cm \
  -V linestretch=1.15 \
  -V colorlinks=true \
  --citeproc \
  --bibliography "${BIB}" \
  -o "${OUTPUT}"

echo "output=${OUTPUT}"
