#!/usr/bin/env python3
"""Generate the synthetic SARS-CoV-2 fixtures for oxo-flow-viralrecon.

The shipped fixtures (400 x 76bp reads with uniform 'I' qualities) fed
nothing downstream: fastp's dedup collapsed them to ~20 reads and SPAdes
rnaviral wrote no assembly at all (live). This generator emits realistic
Illumina data off the bundled 6kb reference: 150bp paired reads at ~50x
(1000 pairs per sample), ~300bp inserts, 0.5% sequencing error, declining
Q38->Q23 qualities, unique start positions (dedup-safe).

Regenerate with:  python3 test/fixtures/generate_fixtures.py
"""
import gzip
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
REF = os.path.abspath(os.path.join(HERE, "..", "..", "reference", "genome.fa"))
HOST = os.path.abspath(os.path.join(HERE, "..", "..", "reference", "host_chr21_slice.fa"))
READ_LEN = 150
INSERT = 300
ERROR_RATE = 0.005
PAIRS_PER_SAMPLE = 1000
HOST_FRACTION = 0.05  # host reads the kraken2 filter is meant to remove
SEED = 42

COMP = str.maketrans("ACGT", "TGCA")


def revcomp(seq):
    return seq[::-1].translate(COMP)


def load_genome(path):
    seq = "".join(
        line.strip()
        for line in open(path)
        if not line.startswith(">")
    )
    return seq.upper()


def qualities(length, rng):
    # stays >= Q30 end to end: viralrecon's fastp runs
    # --qualified_quality_phred 30 --unqualified_percent_limit 10, so a
    # Q38->Q23 decline discards every read (live: 1000 pairs -> 2).
    # Q38->Q32 matches modern Illumina data.
    qs = []
    for i in range(length):
        q = 38 - 6 * (i / length) + rng.gauss(0, 1.0)
        qs.append(chr(33 + int(max(30, min(40, round(q))))))
    return "".join(qs)


def make_reads(template, n_pairs, rng):
    tlen = len(template)
    out1, out2 = [], []
    for _ in range(n_pairs):
        start = rng.randrange(tlen)
        insert = max(READ_LEN, rng.randint(INSERT - 100, INSERT + 100))
        end = start + insert
        frag = (template[start:end] if end <= tlen
                else template[start:] + template[: end - tlen])
        read1 = frag[:READ_LEN]
        read2 = revcomp(frag[insert - READ_LEN : insert])
        read1 = "".join(
            c if rng.random() > ERROR_RATE else rng.choice([b for b in "ACGT" if b != c])
            for c in read1
        )
        read2 = "".join(
            c if rng.random() > ERROR_RATE else rng.choice([b for b in "ACGT" if b != c])
            for c in read2
        )
        out1.append(read1)
        out2.append(read2)
    return out1, out2


def make_sample(sample, genome, host, rng):
    n_host = int(PAIRS_PER_SAMPLE * HOST_FRACTION)
    n_viral = PAIRS_PER_SAMPLE - n_host
    pairs = make_reads(host, n_host, rng) + make_reads(genome, n_viral, rng)
    r1 = [f"@{sample}_{i}/1\n{p[0]}\n+\n{qualities(READ_LEN, rng)}" for i, p in enumerate(pairs)]
    r2 = [f"@{sample}_{i}/2\n{p[1]}\n+\n{qualities(READ_LEN, rng)}" for i, p in enumerate(pairs)]
    # shuffle so host/viral reads interleave like a real sample
    order = list(range(len(pairs)))
    rng.shuffle(order)
    r1 = [r1[i] for i in order]
    r2 = [r2[i] for i in order]
    for suffix, reads in (("R1", r1), ("R2", r2)):
        with gzip.open(os.path.join(RAW, f"{sample}_{suffix}.fastq.gz"), "wt") as fh:
            fh.write("\n".join(reads) + "\n")


def main():
    rng = random.Random(SEED)
    genome = load_genome(REF)
    host = load_genome(HOST)
    print(f"reference: {len(genome)} bp viral + {len(host)} bp host slice")
    for sample in ("S1", "S2"):
        make_sample(sample, genome, host, rng)
        print(f"{sample}: {PAIRS_PER_SAMPLE} pairs ({int(PAIRS_PER_SAMPLE * HOST_FRACTION)} host)")
    print("viralrecon fixtures regenerated: 150bp PE, 50x, 5% host reads, declining qualities")


if __name__ == "__main__":
    main()
