#!/usr/bin/env python3
"""Battery of sanity checks on evo2.db before we wire up Datasette."""
import sqlite3, textwrap

db = sqlite3.connect("/Users/rui/Desktop/papers/NAR/database/evo2_database/evo2.db")
db.row_factory = sqlite3.Row
q = lambda s: db.execute(s).fetchall()
def hr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)

hr("ROW COUNT / UNIQUENESS")
print("total rows           :", q("SELECT count(*) c FROM variants")[0]["c"])
print("distinct variant_id  :", q("SELECT count(DISTINCT variant_id) c FROM variants")[0]["c"])
print("distinct rsid        :", q("SELECT count(DISTINCT rsid) c FROM variants")[0]["c"])

hr("CHROMOSOME COVERAGE (count per CHR)")
for r in q("SELECT CHR, count(*) n, min(BP) lo, max(BP) hi FROM variants GROUP BY CHR ORDER BY n DESC"):
    print(f"  chr {str(r['CHR']):<4} {r['n']:>9,}   BP {r['lo']:>12,} .. {r['hi']:>12,}")

hr("NULL HANDLING (key columns)")
for col in ["evo7b_noRC_delta_score","evo40b_noRC_delta_score","phastCons100way",
            "phyloP100way","Alt_Freq","MAF","Gene_ensGene","AAChange_ensGene"]:
    n = q(f'SELECT count(*) c FROM variants WHERE "{col}" IS NULL')[0]["c"]
    print(f"  NULL in {col:<26}: {n:>10,}")

hr("SCORE DISTRIBUTIONS (delta scores)")
for col in ["evo7b_noRC_delta_score","evo40b_noRC_delta_score"]:
    r = q(f'SELECT min("{col}") lo, max("{col}") hi, avg("{col}") mu FROM variants')[0]
    print(f"  {col:<26}: min={r['lo']:.3f}  max={r['hi']:.3f}  mean={r['mu']:.4f}")

for label, col in [("Func.ensGene","Func_ensGene"),("ExonicFunc.ensGene","ExonicFunc_ensGene"),
                   ("category(cCRE)","category"),("MAF_tier","MAF_tier"),
                   ("repClass","repClass"),("Callrate_filter","Callrate_filter")]:
    hr(f"VALUE COUNTS: {label}")
    for r in q(f'SELECT "{col}" v, count(*) n FROM variants GROUP BY "{col}" ORDER BY n DESC LIMIT 15'):
        print(f"  {str(r['v'])[:45]:<46} {r['n']:>10,}")

hr("TOP GENES BY VARIANT COUNT")
for r in q('SELECT Gene_ensGene v, count(*) n FROM variants WHERE Gene_ensGene IS NOT NULL GROUP BY Gene_ensGene ORDER BY n DESC LIMIT 12'):
    print(f"  {str(r['v'])[:40]:<41} {r['n']:>9,}")

hr("FTS5 SEARCH TEST  (MATCH 'BRCA1')")
rows = q("SELECT v.rsid, v.CHR, v.BP, v.Gene_ensGene, v.evo7b_noRC_delta_score d "
         "FROM variants v JOIN variants_fts f ON v.rowid=f.rowid "
         "WHERE variants_fts MATCH 'BRCA1' LIMIT 5")
print(f"  matched (showing 5 of) ...")
for r in rows:
    print(f"    {r['rsid']}  chr{r['CHR']}:{r['BP']}  {r['Gene_ensGene']}  7b_delta={r['d']}")

hr("POINT LOOKUP  (variant_id = '1:61987:A:G')")
for r in q("SELECT * FROM variants WHERE variant_id='1:61987:A:G'"):
    d = dict(r)
    for k in ["variant_id","rsid","Alt_Freq","evo7b_noRC_delta_score","evo40b_noRC_delta_score",
              "Func_ensGene","Gene_ensGene","category","MAF_tier","phyloP100way"]:
        print(f"    {k:<26}: {d[k]}")

hr("RANGE QUERY PLAN (uses idx_chr_bp?)")
for r in q("EXPLAIN QUERY PLAN SELECT * FROM variants WHERE CHR='1' AND BP BETWEEN 60000 AND 70000"):
    print("   ", r["detail"] if "detail" in r.keys() else tuple(r))

db.close()
