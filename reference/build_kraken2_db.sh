#!/usr/bin/env bash
# Build the minimal kraken2 host-removal database shipped as
# reference/kraken2_db.tar.gz: a single-taxon (SARS-CoV-2, taxid
# 2697049) index over the fixture reference genome, constructed without
# any NCBI downloads so it works offline and in restricted networks.
#
# Usage: bash reference/build_kraken2_db.sh   (requires kraken2 + tar)
set -euo pipefail
cd "$(dirname "$0")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/taxonomy" "$TMP/library"

# minimal taxonomy: 1 = root, 2 = SARS-CoV-2
printf '1\t|\t1\t|\tno rank\t|\n2\t|\t1\t|\tspecies\t|\n' > "$TMP/taxonomy/nodes.dmp"
printf '1\t|\t\t|\troot\t|\t\t|\n' > "$TMP/taxonomy/names.dmp"
printf '2\t|\t\t|\tSevere acute respiratory syndrome coronavirus 2\t|\tscientific name\t|\n' >> "$TMP/taxonomy/names.dmp"
printf 'NC_045512.2\t2\n' > "$TMP/seqid2taxid.map"
cp genome.fa "$TMP/library/virus.fna"

kraken2-build --build --db "$TMP" --threads "${THREADS:-4}"
tar czf kraken2_db.tar.gz -C "$TMP" hash.k2d opts.k2d taxo.k2d
echo "wrote reference/kraken2_db.tar.gz"
