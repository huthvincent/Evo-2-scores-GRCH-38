#!/usr/bin/env python3
"""
Build a Datasette-ready SQLite database from the complete Evo2 inference TSV.

Source : Evo2_6Models_Inference_result.6475639.UCSC_Fullanno.LCR_addMAF_Tier.June10.txt.gz
Output : evo2.db   (table: variants  + FTS + indexes)

Streams the gzip directly (no multi-GB intermediate file). Robust NULL handling
('.', 'NA', '' -> NULL), type inference, leading-digit column rename, a synthetic
variant_id, indexes on the columns users actually query, and an FTS5 index for
free-text search over rsid / gene / amino-acid change.
"""
import csv, gzip, sqlite3, sys, time

SRC = "/Users/rui/Desktop/papers/NAR/database/Evo2_6Models_Inference_result.6475639.UCSC_Fullanno.LCR_addMAF_Tier.June10.txt.gz"
DB  = "/Users/rui/Desktop/papers/NAR/database/evo2_database/evo2.db"

NULL_TOKENS = {"", ".", "NA", "na", "N/A", "NaN", "nan", "None", "null"}
BATCH = 20000

# csv field-size guard (some annotation columns can be long)
csv.field_size_limit(1 << 24)


def clean(col: str) -> str:
    """Sanitize a header name into a safe SQLite identifier, preserving meaning."""
    c = col.strip()
    if c.startswith("7b_"):
        c = "evo7b_" + c[3:]
    elif c.startswith("40b_"):
        c = "evo40b_" + c[4:]
    c = c.replace(".", "_").replace("-", "_").replace(" ", "_")
    return c


def col_type(name: str) -> str:
    """REAL for scores/frequencies/conservation, INTEGER for position, else TEXT."""
    if name == "BP":
        return "INTEGER"
    if "score" in name or name in ("Alt_Freq", "MAF", "phastCons100way", "phyloP100way"):
        return "REAL"
    return "TEXT"


def main():
    t0 = time.time()
    with gzip.open(SRC, "rt", encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        raw_header = next(reader)
        cols = [clean(c) for c in raw_header]
        types = {c: col_type(c) for c in cols}

        # de-duplicate any repeated cleaned names (e.g. a stray duplicate 'category')
        seen, final_cols = {}, []
        for c in cols:
            if c in seen:
                seen[c] += 1
                final_cols.append(f"{c}_{seen[c]}")
            else:
                seen[c] = 0
                final_cols.append(c)
        cols = final_cols
        types = {c: col_type(c) for c in cols}

        real_idx = {i for i, c in enumerate(cols) if types[c] == "REAL"}
        int_idx  = {i for i, c in enumerate(cols) if types[c] == "INTEGER"}
        ncol = len(cols)
        try:
            chr_i = cols.index("CHR"); bp_i = cols.index("BP")
            ref_i = cols.index("Ref"); alt_i = cols.index("Alt")
        except ValueError:
            chr_i = bp_i = ref_i = alt_i = None

        print(f"[schema] {ncol} columns")
        for c in cols:
            print(f"    {c:32s} {types[c]}")
        sys.stdout.flush()

        db = sqlite3.connect(DB)
        db.executescript(
            "PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;"
            "PRAGMA temp_store=MEMORY; PRAGMA cache_size=-400000;"
        )
        coldefs = ",\n  ".join(f'"{c}" {types[c]}' for c in cols)
        db.execute("DROP TABLE IF EXISTS variants")
        db.execute(f'CREATE TABLE variants (\n  variant_id TEXT,\n  {coldefs}\n)')

        placeholders = ",".join(["?"] * (ncol + 1))  # +1 for variant_id
        insert = f"INSERT INTO variants VALUES ({placeholders})"

        def conv(row):
            # pad/truncate defensively
            if len(row) != ncol:
                row = (row + [None] * ncol)[:ncol]
            out = [None] * (ncol + 1)
            for i in range(ncol):
                v = row[i]
                if v is None or v in NULL_TOKENS:
                    out[i + 1] = None
                elif i in real_idx:
                    try: out[i + 1] = float(v)
                    except ValueError: out[i + 1] = None
                elif i in int_idx:
                    try: out[i + 1] = int(float(v))
                    except ValueError: out[i + 1] = None
                else:
                    out[i + 1] = v
            if chr_i is not None:
                c_, b_, r_, a_ = row[chr_i], row[bp_i], row[ref_i], row[alt_i]
                out[0] = f"{c_}:{b_}:{r_}:{a_}"
            return out

        buf, n, truncated = [], 0, False
        try:
            for row in reader:
                buf.append(conv(row))
                if len(buf) >= BATCH:
                    db.executemany(insert, buf); buf.clear()
                    n += BATCH
                    if n % 500000 == 0:
                        print(f"[load] {n:,} rows  {time.time()-t0:,.0f}s"); sys.stdout.flush()
        except (EOFError, OSError) as e:
            truncated = True
            print(f"[warn] source gzip truncated near row {n+len(buf):,}: {e}")
        if buf:
            db.executemany(insert, buf); n += len(buf)
        db.commit()
        print(f"[load] DONE {n:,} rows  truncated={truncated}  {time.time()-t0:,.0f}s"); sys.stdout.flush()

    # indexes on the columns users actually query / facet / sort by
    idx_cols = [
        ("idx_chr_bp", '"CHR","BP"'),
        ("idx_rsid", '"rsid"'),
        ("idx_gene", '"Gene_ensGene"'),
        ("idx_variant", '"variant_id"'),
        ("idx_7b_delta", '"evo7b_noRC_delta_score"'),
        ("idx_40b_delta", '"evo40b_noRC_delta_score"'),
        ("idx_func", '"Func_ensGene"'),
        ("idx_exonic", '"ExonicFunc_ensGene"'),
        ("idx_category", '"category"'),
        ("idx_maf_tier", '"MAF_tier"'),
        ("idx_repclass", '"repClass"'),
    ]
    for name, expr in idx_cols:
        try:
            db.execute(f"CREATE INDEX {name} ON variants({expr})")
            print(f"[index] {name}"); sys.stdout.flush()
        except sqlite3.OperationalError as e:
            print(f"[index] SKIP {name}: {e}")

    # FTS5 free-text search over identifiers / gene / protein change
    fts_cols = [c for c in ("rsid", "Gene_ensGene", "AAChange_ensGene") if c in cols]
    if fts_cols:
        cl = ", ".join(f'"{c}"' for c in fts_cols)
        db.execute(
            f"CREATE VIRTUAL TABLE variants_fts USING fts5({cl}, "
            f"content='variants', content_rowid='rowid')"
        )
        db.execute(
            f"INSERT INTO variants_fts(rowid, {cl}) SELECT rowid, {cl} FROM variants"
        )
        print(f"[fts] indexed {fts_cols}"); sys.stdout.flush()

    print("[analyze] ..."); sys.stdout.flush()
    db.execute("ANALYZE")
    db.commit()
    db.execute("VACUUM")
    db.close()
    print(f"[done] {time.time()-t0:,.0f}s total")


if __name__ == "__main__":
    main()
