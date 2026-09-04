# oxo-flow-viralrecon — Viral assembly and intrahost variant calling for Illumina amplicon data

> ★ Verified · ⇄ Official port of [`nf-core/viralrecon`](https://github.com/nf-core/viralrecon) @ `3.0.0` — same tools, same versions, same commands. Part of the [oxo-flow-community catalog](https://oxo-flow-community.github.io/).

[![CI](https://github.com/oxo-flow-community/oxo-flow-viralrecon/actions/workflows/ci.yml/badge.svg)](https://github.com/oxo-flow-community/oxo-flow-viralrecon/actions/workflows/ci.yml)

This workflow turns paired-end Illumina amplicon reads into a complete viral
genomics report: read QC and trimming (FastQC, fastp), host-sequence removal
(Kraken2), alignment to a user-provided reference genome (Bowtie2), primer
trimming (iVar), intrahost variant calling and annotation (iVar → snpEff /
SnpSift), consensus building with low-coverage masking (bcftools), lineage
assignment and deconvolution (Pangolin, Nextclade, Freyja), de novo assembly
with QC (Cutadapt → SPAdes / Unicycler / minia → Bandage / BLAST / QUAST /
ABACAS / plasmidID — any comma-separated combination), and a single
MultiQC report tying everything together. The repository ships a tiny
end-to-end fixture (2 samples, 200 reads each, a 6 kb SARS-CoV-2-like
reference, and stub Kraken2/Pangolin/Freyja databases) so the workflow can be
exercised without downloading anything; point the `[config]` keys at your own
data to use it for real.

## Installation

### 1. Install oxo-flow

Requires oxo-flow >= 0.17.0 (the fastp empty-reads gates use the `when`
runtime functions shipped in 0.17.0).

Release binary (recommended):

```bash
curl -fL -o oxo-flow.tar.gz https://github.com/Traitome/oxo-flow/releases/latest/download/oxo-flow-latest-x86_64-unknown-linux-gnu.tar.gz
tar xzf oxo-flow.tar.gz && sudo mv oxo-flow /usr/local/bin/
```

Alternative via conda: `conda install -c bioconda oxo-flow-cli` (note: the
conda package may lag behind releases; other platform binaries are on the
[releases page](https://github.com/Traitome/oxo-flow/releases)).

### 2. Get this workflow

```bash
git clone https://github.com/oxo-flow-community/oxo-flow-viralrecon.git
cd oxo-flow-viralrecon
```

### 3. Requirements

**(a) Reference data** — the workflow takes every reference as a local file;
the files shipped in `reference/` are test fixtures, so replace them with real
data before running:

- reference genome FASTA (`config.fasta`, default `reference/genome.fa`) and
  annotation GFF (`config.gff`, default `reference/genome.gff`) — uncompressed,
  or set `fasta_ends_gz` / `gff_ends_gz` to run the gunzip steps first
- primer scheme BED (`config.primer_bed`, default `reference/primers.bed`) for
  the amplicon protocol
- Kraken2 host-removal database as a tar.gz (`config.kraken2_db`, default
  `reference/kraken2_db.tar.gz`)
- Pangolin data directory (`config.pango_database`) and Freyja barcodes /
  lineages CSVs (`config.freyja_barcodes` / `config.freyja_lineages`)
- Nextclade dataset: downloaded automatically (`--name sars-cov-2 --tag
  2024-10-17--16-48-48Z`), or set `config.nextclade_dataset` to a local dataset
  directory to skip the download
- paired-end Illumina FASTQs at `<raw_dir>/<sample>_R1.fastq.gz` and
  `<raw_dir>/<sample>_R2.fastq.gz` (`config.raw_dir`)

**(b) Compute** — resource labels map 1:1 to the upstream `withLabel` profiles
(`process_single` 1c/6 GB, `process_low` 2c/12 GB, `process_medium` 6c/36 GB,
`process_high` 12c/72 GB); the heaviest rules need up to **12 CPUs / 72 GB per
rule**. The oxo-flow resource pool queues work rather than oversubscribing.

**(c) Tool delivery** — conda environments with pinned versions
(`envs/*.yaml`, conda-forge + bioconda channels, exact pins from the upstream
module environment files). No containers. You need conda or mamba installed;
rules create and reuse the pinned environments from `envs/`.

## Usage

```bash
# validate, lint and dry-run the default configuration
./test/run.sh

# or by hand:
oxo-flow validate main.oxoflow
oxo-flow dry-run main.oxoflow --samples first:1
oxo-flow run main.oxoflow --samples first:1
```

### Inputs

Upstream reads samples from a CSV samplesheet
(`sample,fastq_1,fastq_2,platform,protocol`); oxo-flow discovers samples from
the filesystem instead. Place paired-end FASTQ files at
`<raw_dir>/<sample>_R1.fastq.gz` and `<raw_dir>/<sample>_R2.fastq.gz` and set
`raw_dir` (default `test/fixtures/raw`, containing the fixture samples `S1`,
`S2`). Samples are listed in `[[sample_groups]]`.

Upstream can download its reference, primer scheme, Kraken2 database,
Pangolin data and Freyja barcodes over the network (profiles/genomes.config
URLs, `KRAKEN2_BUILD`, `PANGOLIN_UPDATEDATA`, `FREYJA_UPDATE`). The port has no
network steps: all such inputs are files in the repository, with fixtures
provided. Reference files must be uncompressed; set `fasta_ends_gz`,
`gff_ends_gz` or `primer_bed_ends_gz` to `true` to run the equivalent of the
upstream `GUNZIP_*` steps first.

### Configuration

Upstream `params.*` are `[config]` keys with identical defaults:

| key | default | upstream param |
| --- | --- | --- |
| `fasta`, `gff`, `primer_bed` | `reference/genome.fa` etc. | `--fasta`, `--gff`, `--primer_bed` |
| `kraken2_db` | `reference/kraken2_db.tar.gz` | `--kraken2_db` |
| `kraken2_variants_host_filter` | `false` | `--kraken2_variants_host_filter` |
| `kraken2_assembly_host_filter` | `true` | `--kraken2_assembly_host_filter` |
| `nextclade_dataset_name` / `_tag` | `sars-cov-2` / `2024-10-17--16-48-48Z` | `--nextclade_dataset_name/_tag` (MN908947.3 genome config) |
| `pango_database` | `test/fixtures/refs/pangolin_db` | `--pango_database` |
| `freyja_barcodes` / `freyja_lineages` | fixture CSV files | `--freyja_barcodes` / `--freyja_lineages` |
| `freyja_repeats` / `freyja_depthcutoff` | `100` / `0` | `--freyja_repeats` / `--freyja_depthcutoff` |
| `raw_dir` / `out_dir` | `test/fixtures/raw` / `results` | samplesheet / `--outdir` |
| `platform` / `protocol` | `illumina` / `amplicon` | `--platform` / `--protocol` |
| `variant_caller` / `consensus_caller` | `ivar` / `bcftools` | `--variant_caller` / `--consensus_caller` |
| `min_mapped_reads` | `1000` | `--min_mapped_reads` (drop side is a deviation; the reporting half is ported — see deviations) |
| `skip_fastp` | `false` | `--skip_fastp` (when `true` the fastp empty-reads drop is off, matching upstream) |
| `min_contig_length` / `min_perc_contig_aligned` | `200` / `0.7` | `--min_contig_length` / `--min_perc_contig_aligned` |
| `assemblers` / `spades_mode` | `spades` / `rnaviral` | `--assemblers` / `--spades_mode` |
| `primer_left_suffix` / `primer_right_suffix` | `_LEFT` / `_RIGHT` | `--primer_left_suffix` / `--primer_right_suffix` |
| `threeprime_adapters` | `false` | `--threeprime_adapters` |
| all `skip_*` keys | upstream defaults | `--skip_fastqc` etc. (markdup/plasmidid `true`) |
| `multiqc_title` | `""` | `--multiqc_title` |

### Outputs

Everything lands under `out_dir/results` (or the path given by `out_dir`),
mirroring the upstream publishDir layout:

```
results/
├── fastqc/{raw,trim}/                  FastQC reports (raw + fastp-trimmed)
├── fastp/                              fastp JSON/HTML/log per sample
├── kraken2/                            Kraken2 reports + host-filtered reads
├── variants/bowtie2/                   BAMs, logs, picard_metrics, mosdepth/{genome,amplicon}
├── variants/freyja/{variants,demix,bootstrap}/
├── variants/ivar/                      variant TSV/VCF, snpeff/, bcftools_stats/
├── variants/ivar/consensus/bcftools/   filtered VCF, consensus FASTA, quast.consensus,
│                                       pangolin/, nextclade/, base_qc/
├── variants/ivar/variants_long_table.csv
├── assembly/cutadapt/                  primer-trimmed reads, adapters.sub.fa, fastqc/
├── assembly/spades/rnaviral/           scaffolds/contigs/gfa (gzipped), bandage/,
│                                       blastn/, quast.spades/, abacas/, plasmidid/
├── assembly/unicycler/                 scaffolds/gfa (gzipped), bandage/, blastn/,
│                                       quast.unicycler/, abacas/, plasmidid/
├── assembly/minia/                     contigs/unitigs/h5, blastn/, quast.minia/,
│                                       abacas/, plasmidid/
└── multiqc/                            multiqc_report.html, multiqc_data/,
                                        variants_metrics_mqc.csv, assembly_metrics_mqc.csv
```

## Source

- Upstream: [`nf-core/viralrecon`](https://github.com/nf-core/viralrecon) @
  tag `3.0.0` (commit
  `395079f1d24dce731ac22e03d7a5e71f110103fc`)
- Upstream license: MIT (preserved verbatim at
  [LICENSE.upstream](LICENSE.upstream))
- Created 2026-08-15; this workflow may lag behind upstream releases.
- Attribution details: [NOTICE.md](NOTICE.md)

## Fidelity

Every upstream process and subworkflow on the default path, and what happened
to it in this port:

| Upstream process (module) | Port rule | Notes |
| --- | --- | --- |
| CAT_FASTQ | `cat_fastq` | `cat` to `fastp/{sample}_{1,2}.fastq.gz` |
| FASTQC_RAW | `fastqc_raw` | same args; upstream input-rename step kept (reads symlinked to `{sample}_{1,2}.fastq.gz` before FastQC so output names match), then renamed into `results/fastqc/raw/` |
| FASTP | `fastp` | `ext.args` baked in verbatim (cut_front/cut_tail/trim_poly_x/cut_mean_quality 30/...) + `--detect_adapter_for_pe`, `2>| >(tee log >&2)`; `save_trimmed_fail=true` adds upstream's `--failed_out {sample}.paired.fail.fastq.gz --unpaired1/2 {sample}_{1,2}.fail.fastq.gz` (off by default — empty placeholders) |
| FASTQC_TRIM | `fastqc_trim` | same args; upstream input-rename step kept (trimmed reads symlinked to `{sample}_{1,2}.fastq.gz` before FastQC), then renamed into `results/fastqc/trim/` |
| KRAKEN2_KRAKEN2 | `kraken2` | `--db` (local), `--report-zero-counts`, pigz of classified/unclassified pairs; gated on `skip_kraken2` + the fastp empty-reads drop (`reads_count(...) > 0` when-gate) |
| (channel wiring) | `assembly_fastq` | passthrough of fastp reads to `kraken2/{sample}.unclassified_*.fastq.gz` when host filtering is off — replaces upstream `ch_assembly_fastq = ch_variants_fastq`; see deviations |
| BOWTIE2_ALIGN | `align_bowtie2` | index found by `find -L` on `*.rev.1.bt2[l]`, `--local --very-sensitive-local --seed 1`, unmapped-filtered `samtools view -F4`, log tee'd; carries the fastp empty-reads drop when-gate |
| IVAR_TRIM | `ivar_trim` | `-m 30 -q 20 -e` (noprimer-gated), optional `-x offset`, log captured; gated amplicon |
| BAM_SORT_STATS_SAMTOOLS | `bam_sort_index_trimmed` | merged: `samtools cat` (single input, dropped) → sort → index → stats/flagstat/idxstats |
| (align branch) | `bam_sort_index` | same merged trio for the untrimmed BAM |
| PICARD_MARKDUPLICATES | `markduplicates` / `markduplicates_wgs` | gated `skip_markduplicates=false`; `--ASSUME_SORTED true --VALIDATION_STRINGENCY LENIENT --TMP_DIR tmp` + `REMOVE_DUPLICATES=true` when `filter_duplicates`; samtools index + stats/flagstat/idxstats; upstream replaces `ch_bam` with the marked BAM, the port keeps the pre-dedup BAM in the pipeline and publishes the marked BAM alongside (see deviations) |
| PICARD_COLLECTMULTIPLEMETRICS | `picard_metrics` | `-Xmx4800M` (= 6 GB task × 0.8), LENIENT, `--TMP_DIR tmp`, all 5 metric files + pdf |
| MOSDEPTH_AMPLICON | `mosdepth_amplicon` | `--fast-mode --use-median --thresholds 0,1,10,50,100,500 --by collapsed.bed` |
| MOSDEPTH_GENOME | `mosdepth_genome` | `--fast-mode --by 200` |
| PLOT_MOSDEPTH_REGIONS (×2) | `plot_mosdepth_genome` / `plot_mosdepth_amplicon` | glob-gather over `*.regions.bed.gz`, `all_samples.mosdepth.*` outputs |
| FREYJA_VARIANTS | `freyja_variants` | `--ref --variants --depths` |
| FREYJA_DEMIX | `freyja_demix` | `--output --barcodes --meta`, `--depthcutoff` when non-zero |
| FREYJA_BOOT | `freyja_boot` | `--nt --nb {freyja_repeats} --boxplot pdf`, boot outputs renamed to `{sample}.lineages.csv` / `{sample}_summarized.csv` |
| IVAR_VARIANTS | `call_variants_ivar` | `samtools mpileup` (`--ignore-overlaps --count-orphans --no-BAQ --max-depth 0 --min-BQ 0`) \| `ivar variants -t 0.25 -q 20 -m 10 -g -r -p`; `save_mpileup=true` tees the mpileup stream to `variants/ivar/{sample}.mpileup` (off by default — empty placeholder) |
| IVAR_VARIANTS_TO_VCF | `ivar_to_vcf` | `--ignore_strand_bias`, variant-counts log + header-cat MQC tsv |
| BCFTOOLS_SORT | `sort_vcf` | `--output --temp-dir .` (default `--output-type z`); process_medium label (6c/36 GB/8 h) |
| VCF_TABIX_STATS | `sort_vcf` | merged: tabix (`--threads -p vcf -f`) + `bcftools stats` |
| VARIANTS_BCFTOOLS | `call_variants_bcftools` / `call_variants_bcftools_wgs` + `norm_vcf_bcftools` | gated `variant_caller='bcftools'` (amplicon) or `protocol='metagenomic'` (auto, mirroring upstream's derived default — see deviations); mpileup (`--ignore-overlaps --count-orphans --no-BAQ --max-depth 0 --min-BQ 20`) \| `bcftools call` (`--ploidy 1 --multiallelic-caller`) \| reheader \| view `--include 'INFO/DP>=10'`, then `bcftools norm` (`--do-not-normalize --multiallelics -any`) merged with tabix + `bcftools stats` (VCF_TABIX_STATS); canonical `variants/ivar/` VCF paths shared with the ivar caller — 3.0.0 has no BCFTOOLS_MPILEUP_FILTER process, filtering lives in the BCFTOOLS_FILTER consensus-branch process |
| SNPEFF_ANN | `snpeff_ann` | `-Xmx36g`, `-config/-dataDir` locals, `-csvStats`, summary html move |
| VCF_BGZIP_TABIX_STATS | `snpeff_ann` | merged: bgzip + tabix + `bcftools stats` |
| SNPSIFT_EXTRACTFIELDS | `snpsift_extract` | same ANN[*]/EFF[*] field list, `-s "," -e "."` |
| BCFTOOLS_FILTER | `consensus_filter` / `consensus_filter_bcftools` | ivar-caller branch `--include 'FORMAT/ALT_FREQ >= 0.75'`; bcftools-caller branch `--include 'FORMAT/AD[:1] / FORMAT/DP >= 0.75'` (upstream ext.args, both filtered to the same canonical VCF) |
| TABIX_TABIX | `consensus_filter` | merged |
| IVAR_CONSENSUS (CONSENSUS_IVAR) | `consensus_ivar` / `consensus_ivar_wgs` | gated `consensus_caller='ivar'`; `samtools mpileup --count-orphans --no-BAQ --max-depth 0 --min-BQ 0 -aa` \| `ivar consensus -t 0.75 -q 20 -m 10 -n N`; writes the canonical `consensus/bcftools/{sample}.consensus.fa` path so downstream consensus-QC rules are shared (see deviations) |
| MAKE_BED_MASK | `consensus_call` | merged: mpileup `-a` + awk low-coverage (<10) positions + `make_bed_mask.py` |
| BEDTOOLS_MERGE | `consensus_call` | merged |
| BEDTOOLS_MASKFASTA | `consensus_call` | merged |
| BCFTOOLS_CONSENSUS | `consensus_call` | `cat fasta \| bcftools consensus` |
| RENAME_FASTA_HEADER | `consensus_call` | `sed "s/>/>{sample} /g"` (byte-identical to upstream) |
| QUAST (consensus) | `quast_consensus` | `-r --features --threads`, report.tsv symlink; batch run over the whole cohort into one `quast.consensus/` dir — upstream runs one QUAST per sample (`ext.prefix` → per-sample dirs), so MultiQC shows one aggregated sample row here instead of per-sample rows (numeric results equivalent) |
| PANGOLIN_RUN | `pangolin` | `XDG_CACHE_HOME=/tmp/.cache`, `--datadir --outfile --threads` |
| PANGOLIN_UPDATEDATA | `pangolin_updatedata` + `pangolin_run_updated` | gated `pango_database=''`; `pangolin --update-data --datadir reference/pangolin_db` then the same PANGOLIN_RUN shell against the downloaded data |
| NEXTCLADE_RUN | `nextclade` | `--jobs --input-dataset --output-all --output-basename` |
| PLOT_BASE_DENSITY | `plot_base_density` | same script args, `base_qc/` outputs |
| (channel code) | `nextclade_clade_mqc` | upstream builds `nextclade_clade_mqc.tsv` in Nextflow channel code (`getNextcladeFieldMapFromCsv` + `multiqcTsvFromList`); ported as an inline python gather over the per-sample CSVs |
| BCFTOOLS_QUERY | `variants_long_table` | `-H -f '%CHROM\t%POS...'` per sample |
| MAKE_VARIANTS_LONG_TABLE | `variants_long_table` / `variants_long_table_bcftools` | merged with query; symlink-collect pattern, `--variant_caller {config.variant_caller}`; bcftools-caller query reads the AD field (`[%AD\t]`), ivar query reads REF_DP/ALT_DP |
| FREYJA_UPDATE | `freyja_update` + `freyja_demix_updated` / `freyja_boot_updated` | gated when `freyja_barcodes` or `freyja_lineages` is empty; `freyja update --outdir {config.freyja_db_name}` then the same demix/boot shells against the downloaded DB |
| ADDITIONAL_ANNOTATION | `build_snpeff_db_additional` + `additional_annotation` | gated `additional_annotation` non-empty (off by default upstream); snpEff `-gff3` build of the extra annotation in a scratch dir, then per-sample snpEff ann + bgzip/tabix + SnpSift extract + query + `make_variants_long_table.py --variant_caller {config.variant_caller} --output_file additional_variants_long_table.csv` |
| PREPARE_PRIMER_FASTA | `prepare_primer_fasta` | `sed -r '/^[ACTGactg]+$/ s/^/X/g'` |
| CUTADAPT | `cutadapt` | `-Z --cores --overlap 5 --minimum-length 30 --error-rate 0.1 -g file: -G file:` |
| FASTQC (assembly) | `fastqc_primers` | prefix `{sample}.primer_trim` via symlink rename |
| SPADES | `assemble_spades` | `--{config.spades_mode} --memory 72` (upstream `ext.args`; default `rnaviral`), output renames (scaffolds/contigs/gfa gzipped, spades.log) |
| BANDAGE_IMAGE | `bandage` | `--height 1000`, png + svg; upstream GUNZIP_GFA merged in (Bandage 0.9.0 cannot read `.gz` graphs — `gzip -cd` to `{sample}.assembly.gfa` first) |
| BLAST_BLASTN | `blast_assembly` | `-outfmt '6 stitle staxids std slen qlen qcovs'`, DB `find -L *.nin`, header-cat |
| FILTER_BLASTN | `blast_assembly` | merged: awk `$16 > min_contig_length && $18 > min_perc_contig_aligned && $1 !~ /phage/` + header-cat |
| QUAST (assembly) | `quast_assembly` | gunzip of scaffolds in shell, `quast.spades/` dir + tsv symlink; batch run over the whole cohort into one `quast.spades/` dir — upstream runs one QUAST per sample (per-sample `S1.spades/` dirs), so MultiQC shows one aggregated sample row here instead of per-sample rows (numeric results equivalent) |
| ABACAS | `abacas` | `-m -p nucmer`, sorted `.bin`, nucmer delta/filtered/tiling + unused contigs moves |
| UNICYCLER | `assemble_unicycler` | gated on `assemblers` containing `unicycler`; `--threads` in a per-sample scratch dir (unicycler writes generic-named files), `mv assembly.fasta {sample}.scaffolds.fa` + gzip, `assembly.gfa` + log kept; BANDAGE/BLAST/QUAST/ABACAS QC chained as `bandage_unicycler` / `blast_assembly_unicycler` / `quast_assembly_unicycler` / `abacas_unicycler` |
| MINIA | `assemble_minia` | gated on `assemblers` containing `minia`; `-kmer-size 31 -abundance-min 20 -nb-cores {threads} -in input_files.txt`; BLAST/QUAST/ABACAS QC chained as `blast_assembly_minia` / `quast_assembly_minia` / `abacas_minia` (no Bandage: minia has no graph file, upstream runs Bandage only on the unicycler gfa) |
| PLASMIDID | `plasmidid` / `plasmidid_unicycler` / `plasmidid_minia` | gated `skip_plasmidid=false`; one rule per assembler branch, mirroring upstream ASSEMBLY_QC; `--only-reconstruct -C 47 -S 47 -i 60 --no-trim -k 0.80 -d reference/genome.fa` — plasmidID needs no database download (verified: only the reference fasta) |
| KRAKEN2_BUILD | `kraken2_build` | gated `kraken2_db=''`; `kraken2-build --download-taxonomy` + `--download-library {config.kraken2_db_name}` + `--build --threads` into `reference/kraken2_db` (upstream `params.kraken2_db_name`, default `human`) |
| (metagenomic branch) | `mosdepth_genome_wgs` / `picard_metrics_wgs` / `freyja_variants_wgs` / `consensus_call_wgs` / `markduplicates_wgs` / `call_variants_bcftools_wgs` / `consensus_ivar_wgs` | gated `protocol='metagenomic'`; the same shells as their amplicon counterparts running on the untrimmed `sorted.bam`, writing the same canonical outputs (exclusive gates; upstream 3.0.0 protocol enum has no `wgs` value — the port maps the non-amplicon branch to `metagenomic` and calls it `wgs` in rule names) |
| GUNZIP_FASTA/GFF/PRIMER_BED | `gunzip_fasta/gff/primer_bed` | gated on `*_ends_gz`; output to fixed `reference/` paths |
| UNTAR_KRAKEN2_DB | `untar_kraken2_db` | upstream single-top-level-dir strip logic kept + upstream `ext.args2 --no-same-owner` on both tar invocations |
| CUSTOM_GETCHROMSIZES | `prepare_genome` | `samtools faidx` + `cut -f 1,2` |
| COLLAPSE_PRIMERS | `collapse_primers` | `--left_primer_suffix/--right_primer_suffix`; process_medium label (6c/36 GB/8 h) |
| BEDTOOLS_GETFASTA | `get_primer_fasta` | `-s -nameOnly` |
| BOWTIE2_BUILD | `build_bowtie2_index` | `--seed 1 --threads`; process_high label (12c/72 GB/16 h) |
| NEXTCLADE_DATASETGET | `get_nextclade_dataset` | `--name sars-cov-2 --tag 2024-10-17--16-48-48Z` (v3pl tag of the MN908947.3 genome config); skips when a local `nextclade_dataset` path is set |
| BLAST_MAKEBLASTDB | `make_blast_db` | `-parse_seqids -dbtype nucl` |
| SNPEFF_BUILD | `build_snpeff_db` | `-Xmx12g`, `-gff3`, genomes/genome symlinks, `snpeff.config` echo |
| MULTIQC | `multiqc` | both passes kept (parse pass + `-e general_stats --ignore *nextclade_clade_mqc.tsv` final pass), `grep -q ">skip_assembly<"` / `>skip_variants<` / `platform=illumina` rm rules, `multiqc_config_illumina.yml`; inputs mirror upstream `ch_multiqc_files` — snpeff `-csvStats` per-sample csv added (SnpEff section), mosdepth fed as genome `global.dist.txt` (distribution plots) + amplicon `all_samples.mosdepth.coverage.tsv` (heatmap), with the genome `summary.txt` additionally kept for the General Stats table (the inert genome coverage.tsv and amplicon per-sample summary.txt are not fed); the runtime-filter reporting half is ported (fail_mapped_reads_mqc.tsv / fail_mapped_samples_mqc.tsv custom content, same headers/rows as upstream `multiqcTsvFromList`, written only when samples fail) |
| multiqc_to_custom_csv.py | `multiqc` | merged, `--platform illumina` → `variants_metrics_mqc.csv` / `assembly_metrics_mqc.csv` |

Ported branches (all gated off by default, mirroring the upstream
`params` defaults; the default run is byte-for-byte the amplicon ivar path):

- `variant_caller='bcftools'` — VARIANTS_BCFTOOLS (`call_variants_bcftools`,
  `norm_vcf_bcftools`), BCFTOOLS_FILTER (`consensus_filter_bcftools`) and the
  bcftools long table (`variants_long_table_bcftools`); activates with
  `--arg variant_caller=bcftools`, deactivating the ivar caller chain
- `consensus_caller='ivar'` — CONSENSUS_IVAR (`consensus_ivar`) with
  `--arg consensus_caller=ivar`
- non-amplicon (shotgun / "wgs") protocol — `--arg protocol=metagenomic`;
  the untrimmed-BAM counterparts `mosdepth_genome_wgs`, `picard_metrics_wgs`,
  `freyja_variants_wgs`, `consensus_call_wgs`, `markduplicates_wgs`,
  `call_variants_bcftools_wgs`, `consensus_ivar_wgs`; upstream derives
  `variant_caller='bcftools'` for non-amplicon runs (nextflow.config), and the
  port mirrors that derivation in the wgs rules' when conditions — a
  metagenomic run needs no extra `--arg`, the bcftools caller chain
  (`call_variants_bcftools_wgs`, `norm_vcf_bcftools`,
  `consensus_filter_bcftools`, `variants_long_table_bcftools`) runs
  automatically and the iVar caller chain stays amplicon-gated
- alternative assemblers — `--arg assemblers=unicycler` /
  `--arg assemblers=minia` or any comma-separated combination
  (`--arg assemblers=spades,unicycler` runs both in one run, like upstream)
  with their full QC chains (Bandage for spades and unicycler, matching
  upstream; plasmidID per assembler like upstream ASSEMBLY_QC)
- PICARD_MARKDUPLICATES — `--arg skip_markduplicates=false`
- PLASMIDID — `--arg skip_plasmidid=false` (no database download; verified
  upstream uses only the reference fasta)
- network downloads — `kraken2_build` (leave `kraken2_db` empty),
  `freyja_update` (leave `freyja_barcodes`/`freyja_lineages` empty),
  `pangolin_updatedata` (leave `pango_database` empty)
- ADDITIONAL_ANNOTATION — `--arg additional_annotation=path/to.gff`

Still excluded (see metadata.json): the nanopore platform
(ARTIC_GUPPYPLEX/ARTIC_MINION/NANOPLOT/PYCOQC/VCFLIB_VCFUNIQ — upstream
wires per-barcode read channels with single-end meta flags, guppybasecaller
is a commercial ONT tool and no nanopore fixture exists; structural) and the
remaining runtime-filter DROPS — the `min_mapped_reads` flagstat gate and the
zero-variant-sample filters (their reporting half is ported inside the
multiqc rule — see deviations).

### Documented deviations

Everything below has no oxo-flow equivalent and is the closest faithful
approximation; none silently change results:

1. **`config.assemblers` is a comma-separated list in canonical lowercase
   form (commas, no spaces).** The upstream `params.assemblers` accepts any
   comma-separated combination — e.g. `spades,unicycler` runs SPAdes AND
   Unicycler in the same run — trimming and lowercasing each entry. oxo-flow
   `when` conditions have no `in`/contains operator, so the port enumerates
   every combination of the three assemblers with explicit equality tests:
   each assembler family (`assemble_*` plus its Bandage/BLAST/QUAST/ABACAS/
   plasmidID QC chain) is gated on a disjunction of the four combinations
   that contain it. Spelling the list with spaces (`spades, unicycler`) is
   not accepted — upstream's trim is not reproducible without an `in`
   operator. (Negative equality gates were rejected as incorrect:
   `!= 'spades'` would wrongly enable `minia` for
   `assemblers = 'spades,unicycler'`.)
2. **Runtime-filter DROPS are partially ported (engine 0.17.0 `when`
   runtime functions).** The upstream fastp filter (drop samples with 0
   reads after trimming, wrapped in `if (!params.skip_fastp)`) IS ported:
   the consumers of the trimmed reads (`kraken2`, `align_bowtie2`,
   `assembly_fastq`) carry a
   `!config.skip_fastp && reads_count('fastp/{sample}_1.fastp.fastq.gz') > 0`
   gate, matching upstream's per-sample channel drop with the same
   short-circuit. The `min_mapped_reads` flagstat gate (a strict `>` on the
   mapped count parsed out of samtools flagstat text) and the
   zero-variant-sample filters still run in Nextflow channel code with no
   engine equivalent — a sample cannot be dropped mid-DAG from a flagstat
   regex or a `bcftools stats` record count. The reporting half IS ported:
   the multiqc rule regenerates upstream's custom-content TSVs
   (`fail_mapped_reads_mqc.tsv` from the fastp JSONs, `fail_mapped_samples_mqc.tsv`
   from the Bowtie2 flagstats, same headers/rows as `multiqcTsvFromList`),
   written only when samples fail. `min_mapped_reads` config feeds that
   flagstat comparison. Placeholder artifacts (`: > {sample}.scaffolds.fa`
   etc.) stand in where upstream would drop an empty assembly from the
   channel; zero-variant samples keep flowing downstream with a
   placeholder-header VCF (see `ivar_to_vcf`).
3. **MarkDuplicates does not replace `ch_bam`.** Upstream
   `BAM_MARKDUPLICATES_PICARD` swaps `ch_bam` so mosdepth, picard metrics and
   variant calling all consume the marked BAM. The port publishes the marked
   BAM (bam/bai/stats/flagstat/idxstats/metrics) as standalone rules
   (`markduplicates`, `markduplicates_wgs`) while the pipeline keeps the
   pre-dedup BAM — the upstream module itself forbids same-name in/out, and a
   canonical-path swap is impossible in oxo-flow (the rule would read and
   write the same path).
4. **Consensus paths are canonicalised across callers.** Upstream ivar
   consensus publishes under `consensus/ivar/` and bcftools under
   `consensus/bcftools/`. The port's ivar caller writes the canonical
   `variants/ivar/consensus/bcftools/{sample}.consensus.fa` path so
   QUAST/Pangolin/Nextclade/base-density/MultiQC rules are shared across
   both callers with no duplicate outputs.
5. **Kraken2 host-filter routing.** When Kraken2 runs with
   `kraken2_assembly_host_filter=false`, upstream routes the assembly branch
   to the fastp reads (channel wiring) while Kraken2 still writes its
   unclassified FASTQs. The port models this with the `assembly_fastq`
   passthrough rule, which overwrites the `kraken2/` unclassified paths with
   copies of the fastp reads (it runs after `kraken2` when both are active, so
   the content is deterministic).
6. **`nextclade_clade_mqc.tsv`** is built by inline python instead of Nextflow
   channel code (same input CSVs, same output columns).
7. **`min_contig_length` / `min_perc_contig_aligned`** are used directly in the
   BLAST filter awk expression (upstream interpolates the same params).
8. **Condensed environments.** Rules that merge several upstream processes
   consolidate their conda envs. Exact pins are kept; only conflicts are
   resolved: `sed` 4.8 (cat/fastq, gunzip, untar) vs 4.9 (prepare_primer_fasta,
   filter_blastn, rename_fasta_header) → 4.8 in `coreutils.yaml`, 4.9 in
   `blast.yaml`/`consensus.yaml`; make_bed_mask's samtools 1.14 → 1.22.1 in
   `consensus.yaml`; tabix's htslib 1.21 → 1.22.1 in `bcftools.yaml`;
   r-base 4.2 → 4.2.0 in `r.yaml`; mosdepth's build string
   `=0.3.11=h0ec343a_1` → `=0.3.11` for cross-platform resolution.
9. **QUAST/ABACAS/Bandage inputs** gated by upstream `file(...)` existence
   checks (e.g. empty scaffolds) run unconditionally in the port; on the
   fixture and real data the files always exist.
10. **`save_unaligned` / `save_reference` are effectively always on.** The
    Kraken2 unclassified reads feed the assembly branch via upstream channel
    wiring (not a publish gate), so they always land in `kraken2/`; the
    reference files feed every rule and always publish. Both flags are kept as
    config for documentation. (`save_ivar_trimmed_bam` does not exist at
    3.0.0 — only `save_reference`, `save_trimmed_fail`, `save_unaligned` and
    `save_mpileup` do; the latter two are now ported as in-rule switches.)
11. **The upstream `multiqc_data/versions.yml` and `*_plots` outputs are not
    emitted — at parity, not a deviation.** Verified at the pinned 3.0.0 tag:
    the MULTIQC call receives no versions channel and the config has no
    software_versions dict; MultiQC 1.31's search pattern for the software
    table is `.+_mqc_versions\.(yaml|yml)` (plain `versions.yml` is not
    picked up), and `export_plots` defaults false (flat threshold 2000), so
    upstream emits neither artifact on its default path — matching the port.

### Resources

Resource labels map 1:1 to upstream `withLabel` profiles: `process_single`
(1c/6 GB/4 h), `process_low` (2c/12 GB/4 h), `process_medium`
(6c/36 GB/8 h), `process_high` (12c/72 GB/16 h). Fastp/SPAdes memory and
`-Xmx` JVM sizes are derived from the same values as upstream.

## Test

```bash
bash test/run.sh
```

Runs `oxo-flow validate` + `lint` + `dry-run` against the default
configuration (the repo's fixture samples; nothing is downloaded or
executed).

## License

This workflow is Apache-2.0 (see [LICENSE](LICENSE) and
[NOTICE](NOTICE.md)). It is a port of nf-core/viralrecon, which is MIT
licensed — the upstream license is preserved verbatim at
[LICENSE.upstream](LICENSE.upstream).
