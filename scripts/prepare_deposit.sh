#!/usr/bin/env bash
# Assemble the files for the Zenodo deposit in deposit/ (git-ignored).
# Run from the repository root after committing:  bash scripts/prepare_deposit.sh
set -euo pipefail

VERSION="v0.1"
STEM="AnguloLopez_2026_SER2027_poster_${VERSION}"
OUT="deposit"

if [ -n "$(git status --porcelain -- poster scripts img codemeta.json CITATION.cff)" ]; then
    echo "Uncommitted changes in the deposited files; commit them first so the zip matches the PDF." >&2
    exit 1
fi

rm -rf "$OUT"
mkdir -p "$OUT"
cp poster/poster.pdf "$OUT/${STEM}.pdf"
cp poster/poster.png "$OUT/${STEM}_preview.png"
git archive --format=zip --prefix="ser2027-${VERSION}/" -o "$OUT/ser2027-${VERSION}-source.zip" HEAD

# Description for the Zenodo editor: the abstract paragraph from abstract.md, as HTML
python3 - "$OUT/description.html" <<'EOF'
import html, re, sys
text = open("abstract.md", encoding="utf-8").read()
abstract = text.split("## Abstract", 1)[1].split("**Keywords**", 1)[0].strip()
parts = [
    f"<p>{html.escape(abstract)}</p>",
    "<p>Poster for the 12th SER World Conference on Ecological Restoration (Lisbon, 30 August to 3 September 2027), "
    "thematic series Lands in Motion. Every figure is computed from the Côa Valley Eco-Connectivity v6 data bundle "
    "by the code in the repository. These are screening maps, not release sites.</p>",
    "<p>Code and source files: "
    '<a href="https://github.com/coa-connectivity-lab/ser2027">github.com/coa-connectivity-lab/ser2027</a>.</p>',
]
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(parts) + "\n")
EOF

( cd "$OUT" && sha256sum ./*.pdf ./*.png ./*.zip > SHA256SUMS )
echo "Deposit files in $OUT/ (commit $(git rev-parse --short HEAD)):"
ls -la "$OUT"
