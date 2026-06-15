---
license: apache-2.0
language:
  - en
tags:
  - genomics
  - variant-effect-prediction
  - evo2
  - dna-language-model
  - human-genetics
pretty_name: Evo2 Variant Effect Database
size_categories:
  - 1M<n<10M
configs:
  - config_name: default
    data_files: "evo2.parquet"
---

# Evo2 Variant Effect Database

Genome-scale variant-effect predictions from the **Evo2** DNA foundation model
(7B and 40B parameters) for **6,475,578 common autosomal human variants**.

| | |
|---|---|
| **Genome build** | GRCh38 |
| **Variants** | 6,475,578 (autosomes chr1–22; X/Y/MT not included) |
| **Selection** | common variants, gnomAD NFE **MAF ≥ 5%**, call-rate QC passed |
| **Models** | Evo2-7B and Evo2-40B |
| **Scores per model** | log-likelihood for REF & ALT and their delta, under 3 reverse-complement strategies (noRC / avgRC / weightRC) |
| **Annotation** | ANNOVAR/Ensembl gene & exonic function, RepeatMasker, ENCODE cCRE category, phastCons/phyloP 100-way, gnomAD AF & MAF tier |
| **License** | Apache-2.0 |

> **Interpretation.** The delta score is `score(ALT) − score(REF)` of the Evo2 model's
> sequence log-likelihood. More negative = the ALT allele is more disfavored by the model
> (predicted more disruptive). Magnitude is on the model's log-likelihood scale, not a
> calibrated probability. **For research use only — not validated for clinical use.**

## Files

| File | Size | Use |
|------|------|-----|
| `evo2.parquet` | ~796 MB | columnar table — fast download, DuckDB / pandas / Polars |
| `evo2.db` | ~3.4 GB | SQLite database powering the [Datasette](https://datasette.io) web UI + API |
| `Dictionary.txt` | — | column descriptions |

## Data dictionary (38 columns)

| Column | Type | Description |
|--------|------|-------------|
| `CHR` | text | Chromosome (1–22) |
| `BP` | int | Base-pair position (GRCh38) |
| `rsid` | text | dbSNP Reference SNP ID |
| `Ref` / `Alt` | text | Reference / alternate allele |
| `Alt_Freq` | real | Alternate-allele frequency (gnomAD NFE) |
| `MAF` | real | Minor allele frequency |
| `MAF_tier` | text | MAF quintile (Q1 lowest … Q5 highest) |
| `Callrate_filter` | text | Call-rate QC flag (all `passed`) |
| `repName` / `repClass` / `repFamily` | text | RepeatMasker repeat name / class / family |
| `7b_noRC_score_alt` / `_ref` / `_delta_score` | real | Evo2-7B log-likelihood ALT / REF / delta (no RC) |
| `7b_avgRC_*` | real | Evo2-7B, averaged over forward + reverse complement |
| `7b_weightRC_*` | real | Evo2-7B, length-weighted RC |
| `40b_noRC_*` / `40b_avgRC_*` / `40b_weightRC_*` | real | Evo2-40B, same three strategies |
| `Func.ensGene` | text | Region class (intergenic, intronic, exonic, UTR…) |
| `Gene.ensGene` | text | Ensembl gene symbol(s) |
| `GeneDetail.ensGene` | text | Transcript / distance detail |
| `ExonicFunc.ensGene` | text | Coding consequence (nonsynonymous / synonymous / stopgain…) |
| `AAChange.ensGene` | text | Amino-acid change & transcript (coding variants) |
| `phastCons100way` | real | phastCons conservation, 100-way vertebrate (0–1) |
| `phyloP100way` | real | phyloP conservation, 100-way vertebrate (signed) |
| `category` | text | ENCODE cCRE functional category |

Missing values are stored as NULL (source tokens `.` / `NA`). In the Datasette
build, column dots are replaced by underscores and the `7b`/`40b` prefixes by
`evo7b`/`evo40b`, plus a `variant_id` = `CHR:BP:Ref:Alt` key.

## Quick start

```python
# pandas
import pandas as pd
df = pd.read_parquet("hf://datasets/huthvincent/Evo2-Variant-DB/evo2.parquet")

# DuckDB — query 6.5M rows without loading into memory
import duckdb
duckdb.sql("""
  SELECT rsid, CHR, BP, "40b_noRC_delta_score"
  FROM 'hf://datasets/huthvincent/Evo2-Variant-DB/evo2.parquet'
  WHERE "Gene.ensGene" LIKE '%BRCA1%'
  ORDER BY abs("40b_noRC_delta_score") DESC LIMIT 20
""")
```

Interactive browse / search / SQL / JSON API: see the companion Datasette Space.

## Citation

```bibtex
@misc{evo2_variant_db,
  title  = {Evo2 Variant Effect Database},
  author = {<authors>},
  year   = {2026},
  note   = {Pre-submission, Nucleic Acids Research Database Issue},
  url    = {https://huggingface.co/datasets/huthvincent/Evo2-Variant-DB}
}
```

Built with the Evo2 model — please also cite the original Evo2 publication (Arc Institute).
