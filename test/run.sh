#!/usr/bin/env bash
# Acceptance test for oxo-flow-viralrecon port.
# Usage: ./test/run.sh            (uses ./main.oxoflow)
set -euo pipefail
cd "$(dirname "$0")/.."
OXO=${OXO:-oxo-flow}

echo "==> validate"
"$OXO" validate main.oxoflow

echo "==> lint (warnings are acceptable, errors are not)"
"$OXO" lint main.oxoflow

echo "==> dry-run with default config"
# oxo-flow v0.11.0 prints the plan to stderr; capture both streams
"$OXO" dry-run main.oxoflow --samples first:1 > /tmp/oxo-dryrun-$$.txt 2>&1
grep -q "would execute" /tmp/oxo-dryrun-$$.txt

echo "==> debug: expanded commands contain no literal {wildcards}"
"$OXO" debug main.oxoflow 2>&1 | grep -q '{sample}' && { echo "unexpanded wildcards in debug output"; exit 1; } || true

echo "==> nanopore platform branch (TDD branch-flip)"
# flip platform to nanopore in a copy INSIDE the repo dir (metadata_file and
# other relative paths resolve against the config file's directory)
sed -e 's/^platform = "illumina"$/platform = "nanopore"/' main.oxoflow > test_np.oxoflow
trap 'rm -f test_np.oxoflow' EXIT

"$OXO" validate test_np.oxoflow

"$OXO" dry-run test_np.oxoflow --samples first:1 > /tmp/oxo-np-$$.txt 2>&1 || {
    cat /tmp/oxo-np-$$.txt
    exit 1
}
# the nanopore run set must include the platform-specific rules; the plan
# marks non-executing rules with "[skip: ...]", so match "[run:" lines only
for rule in artic_guppyplex artic_minion filter_bam_samtools_nanopore mosdepth_genome_nanopore kraken2_nanopore barcode_qc_manifest; do
    grep -E "^[[:space:]]*[0-9]+\. ${rule}" /tmp/oxo-np-$$.txt | grep -q "\[run:" || { echo "nanopore plan missing rule: $rule"; exit 1; }
done
# ...and must NOT contain the illumina-only chains
for rule in fastqc_raw fastp align_bowtie2 ivar_trim assemble_spades markduplicates; do
    if grep -E "^[[:space:]]*[0-9]+\. ${rule}" /tmp/oxo-np-$$.txt | grep -q "\[run:"; then
        echo "nanopore plan must not contain illumina rule: $rule"
        exit 1
    fi
done

echo "PASS"
