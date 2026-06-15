---
title: Evo2 Variant Effect Database
emoji: 🧬
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: true
license: apache-2.0
short_description: Evo2 variant-effect scores for 6.48M human variants
---

# Evo2 Variant Effect Database

A [Datasette](https://datasette.io) interface to Evo2 DNA foundation-model
variant-effect predictions for **6,475,578 common autosomal human variants**
(GRCh38, chr1–22, gnomAD NFE MAF ≥ 5%).

Browse, full-text search (rsID / gene / AA change), filter by facets, run SQL,
hit the JSON API, or use the canned lookups (by rsID, by region, top-impact by gene).

## Configuration

This Space serves a SQLite database that is **not** committed to the Space repo.
On startup `entrypoint.sh` downloads it from a HuggingFace dataset:

| Variable | Value |
|----------|-------|
| `DB_URL` | `https://huggingface.co/datasets/<user>/<repo>/resolve/main/evo2.db` |

Set it under **Settings → Variables and secrets → New variable** (`DB_URL`).

> Free CPU Spaces use ephemeral storage, so the database is re-downloaded on each
> cold start (~3.4 GB). To avoid this, enable **persistent storage** in Space
> settings, or serve the smaller `evo2.parquet` via the `datasette-parquet` plugin.

## Data

See the dataset card for the full data dictionary, scope, and citation.
For research use only — not validated for clinical interpretation.
