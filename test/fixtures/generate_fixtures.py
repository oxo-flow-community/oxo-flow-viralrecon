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
READ_LEN = 150
INSERT = 300
ERROR_RATE = 0.005
PAIRS_PER_SAMPLE = 1000
SEED = 42

COMP = str.maketrans("ACGT", "TGCA")


def revcomp(seq):
    return seq[::-1].translate(COMP)


def load_genome():
    seq = "".join(
        line.strip()
        for line in open(REF)
        if not line.startswith(">")
    )
    return seq.upper()


def qualities(length, rng):
    qs = []
    for i in range(length):
        q = 38 - 15 * (i / length) + rng.gauss(0, 1.5)
        qs.append(chr(33 + int(max(2, min(40, round(q))))))
    return "".join(qs)


def make_sample(sample, genome, rng):
    glen = len(genome)
    r1, r2 = [], []
    for i in range(PAIRS_PER_SAMPLE):
        start = rng.randrange(glen)
        insert = max(READ_LEN, rng.randint(INSERT - 100, INSERT + 100))
        end = start + insert
        frag = (genome[start:end] if end <= glen
                else genome[start:] + genome[: end - glen])
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
        r1.append(f"@{sample}_{i}/1\n{read1}\n+\n{qualities(READ_LEN, rng)}")
        r2.append(f"@{sample}_{i}/2\n{read2}\n+\n{qualities(READ_LEN, rng)}")
    for suffix, reads in (("R1", r1), ("R2", r2)):
        with gzip.open(os.path.join(RAW, f"{sample}_{suffix}.fastq.gz"), "wt") as fh:
            fh.write("\n".join(reads) + "\n")


def main():
    rng = random.Random(SEED)
    genome = load_genome()
    print(f"reference: {len(genome)} bp")
    for sample in ("S1", "S2"):
        make_sample(sample, genome, rng)
        print(f"{sample}: {PAIRS_PER_SAMPLE} pairs")
    print("viralrecon fixtures regenerated: 150bp PE, 50x, declining qualities")


if __name__ == "__main__":
    main()
