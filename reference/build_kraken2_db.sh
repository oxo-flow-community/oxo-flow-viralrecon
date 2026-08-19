#!/usr/bin/env bash
# Build the minimal kraken2 HOST-removal database shipped as
# reference/kraken2_db.tar.gz: a single-taxon (Homo sapiens, taxid
# 9606) index over the bundled 6kb chr21 slice, constructed without
# any NCBI downloads so it works offline and in restricted networks.
# Viral reads pass through UNCLASSIFIED — the kraken2 step filters
# host reads, so the DB must cover the host, not the virus (live: a
# virus-indexed DB classified 100% of the reads and everything
# downstream ran empty).
#
# Usage: bash reference/build_kraken2_db.sh   (requires kraken2 + tar)
set -euo pipefail
cd "$(dirname "$0")"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/taxonomy" "$TMP/library"

# minimal taxonomy: 1 = root, 2 = Homo sapiens
printf '1\t|\t1\t|\tno rank\t|\n2\t|\t1\t|\tspecies\t|\n' > "$TMP/taxonomy/nodes.dmp"
printf '1\t|\t\t|\troot\t|\t\t|\n' > "$TMP/taxonomy/names.dmp"
printf '2\t|\t\t|\tHomo sapiens\t|\tscientific name\t|\n' >> "$TMP/taxonomy/names.dmp"
printf 'chr21_5010000_5016000\t2\n' > "$TMP/seqid2taxid.map"
cp host_chr21_slice.fa "$TMP/library/host.fna"

kraken2-build --build --db "$TMP" --threads "${THREADS:-4}"
tar czf kraken2_db.tar.gz -C "$TMP" hash.k2d opts.k2d taxo.k2d
echo "wrote reference/kraken2_db.tar.gz"
