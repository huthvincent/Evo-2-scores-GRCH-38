# Evo2 Variant Effect Database — build & deploy kit

Turns the Evo2 inference TSV into a free, public, queryable web database
(Datasette: browse · faceted search · full-text search · SQL · JSON API · canned lookups)
for the NAR Database Issue pre-submission inquiry.

## Live resource

- **Database (web app):** https://huthvincent-evo2-database.hf.space
- **HuggingFace Space:** https://huggingface.co/spaces/huthvincent/evo2-database
- **Data (Parquet + SQLite — download / HF Viewer):** https://huggingface.co/datasets/huthvincent/Evo2-Variant-DB

> The large data files (`evo2.db` ≈ 3.4 GB, `evo2.parquet` ≈ 796 MB) are **not** in this
> repo — they live on the HuggingFace dataset above. This repo holds the code, config, and
> front-end; rebuild the database locally with `build_db.py`.

## What's here

| File / dir | What |
|---|---|
| `build_db.py` | Stream the source `.gz` → `evo2.db` (typed schema, NULL handling, 11 indexes, FTS5, `variant_id`). Tolerates the truncated source. |
| `verify_db.py` | Sanity battery (coverage, uniqueness, NULLs, score ranges, FTS, query plans). |
| `evo2.db` | SQLite, **6,475,578 rows**, ~3.4 GB — served by Datasette. |
| `evo2.parquet` | ZSTD Parquet, ~796 MB — download / DuckDB / pandas / HF viewer. |
| `metadata.yml` | Datasette config: titles, per-column docs, facets, sortable cols, 4 canned queries. |
| `space/` | HuggingFace Docker Space (Datasette) — `Dockerfile`, `entrypoint.sh`, `metadata.yml`, `README.md`. |
| `dataset/README.md` | HuggingFace dataset card + full 38-column data dictionary. |
| `DEPLOY.md` | Step-by-step: HF Space (free) **or** Cloud Run (one command) + domain + Zenodo DOI. |
| `NAR_inquiry.md` | Pre-submission inquiry letter (generated + adversarially audited). |

## Rebuild from a clean source

```bash
python3 build_db.py        # edit SRC at the top if the path changes
python3 verify_db.py
./.venv/bin/python -c "import duckdb;duckdb.connect().execute(\"INSTALL sqlite;LOAD sqlite;ATTACH 'evo2.db' AS s (TYPE SQLITE);COPY (SELECT * FROM s.variants) TO 'evo2.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)\")"
```

## Serve locally

```bash
./.venv/bin/datasette -i evo2.db -m metadata.yml --port 8765   # → http://127.0.0.1:8765
```

## Verified scope (state this in the paper)

- 6,475,578 common autosomal variants (chr1–22; **no X/Y/MT**), GRCh38, gnomAD NFE MAF ≥ 5%.
- Evo2-7B & Evo2-40B; REF/ALT/delta log-likelihood × 3 RC strategies (delta = ALT−REF).
- Overwhelmingly noncoding: ~2.61M intergenic, ~2.18M intronic, ~37.9k coding.
- Every variant unique by rsID and by CHR:BP:Ref:Alt.
- **Caveat:** source `.gz` was truncated (~60–166 tail rows missing of 6,475,639). Re-export
  a clean `.gz` and rerun before the public release to recover them.
