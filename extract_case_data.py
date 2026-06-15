#!/usr/bin/env python3
"""Pull aggregates / samples from evo2.db for the NAR case-study figure panels."""
import sqlite3, json, random

db = sqlite3.connect("/Users/rui/Desktop/papers/NAR/database/evo2_database/evo2.db")
db.row_factory = sqlite3.Row
q = lambda s, p=(): [dict(r) for r in db.execute(s, p).fetchall()]
out = {}

# A. delta distribution by functional region class (sampled values for violins)
func_classes = ["exonic", "UTR3", "UTR5", "ncRNA_exonic", "intronic",
                "ncRNA_intronic", "intergenic", "upstream", "downstream"]
out["delta_by_func"] = {}
for fc in func_classes:
    rows = q("SELECT evo40b_noRC_delta_score d FROM variants "
             "WHERE Func_ensGene=? AND evo40b_noRC_delta_score IS NOT NULL "
             "ORDER BY RANDOM() LIMIT 8000", (fc,))
    if rows:
        out["delta_by_func"][fc] = [r["d"] for r in rows]

# B. delta distribution by coding consequence (ExonicFunc)
exonic = ["synonymous SNV", "nonsynonymous SNV", "stopgain", "stoploss",
          "startloss", "nonframeshift substitution", "frameshift substitution"]
out["delta_by_exonic"] = {}
for ef in exonic:
    rows = q("SELECT evo40b_noRC_delta_score d FROM variants "
             "WHERE ExonicFunc_ensGene=? AND evo40b_noRC_delta_score IS NOT NULL "
             "ORDER BY RANDOM() LIMIT 8000", (ef,))
    if rows:
        out["delta_by_exonic"][ef] = [r["d"] for r in rows]

# C. 7B vs 40B concordance (uniform sample) + Pearson on the sample
sc = q("SELECT evo7b_noRC_delta_score a, evo40b_noRC_delta_score b FROM variants "
       "WHERE rowid % 350 = 0 AND evo7b_noRC_delta_score IS NOT NULL "
       "AND evo40b_noRC_delta_score IS NOT NULL")
out["scatter_7b_40b"] = {"x": [r["a"] for r in sc], "y": [r["b"] for r in sc]}

# D. conservation (phyloP) vs mean |40B delta|, binned
out["phylop_bins"] = q(
    "SELECT CAST(round(phyloP100way) AS INT) bin, "
    "avg(abs(evo40b_noRC_delta_score)) mean_absdelta, count(*) n "
    "FROM variants WHERE phyloP100way IS NOT NULL "
    "GROUP BY bin HAVING n>=200 ORDER BY bin")

# E. BRCA1 variant landscape (all)
out["brca1"] = q(
    "SELECT BP, evo7b_noRC_delta_score d7, evo40b_noRC_delta_score d40, "
    "ExonicFunc_ensGene ef, Func_ensGene fc FROM variants "
    "WHERE Gene_ensGene LIKE '%BRCA1%' AND evo40b_noRC_delta_score IS NOT NULL ORDER BY BP")

# F. cCRE category summary
out["ccre"] = q(
    "SELECT category, count(*) n, avg(evo40b_noRC_delta_score) mean_delta, "
    "avg(abs(evo40b_noRC_delta_score)) mean_absdelta FROM variants "
    "WHERE category IS NOT NULL GROUP BY category ORDER BY n DESC")

# G. overall delta histograms (sample) for 7B and 40B
hh = q("SELECT evo7b_noRC_delta_score a, evo40b_noRC_delta_score b FROM variants "
       "WHERE rowid % 120 = 0")
out["hist"] = {"d7": [r["a"] for r in hh if r["a"] is not None],
               "d40": [r["b"] for r in hh if r["b"] is not None]}

# functional class counts (for context)
out["func_counts"] = q("SELECT Func_ensGene f, count(*) n FROM variants GROUP BY f ORDER BY n DESC")

json.dump(out, open("/Users/rui/Desktop/papers/NAR/database/figures/case_data.json", "w"))
print("delta_by_func groups:", list(out["delta_by_func"].keys()))
print("delta_by_exonic groups:", {k: len(v) for k, v in out["delta_by_exonic"].items()})
print("scatter n:", len(out["scatter_7b_40b"]["x"]))
print("phylop bins:", len(out["phylop_bins"]))
print("brca1 variants:", len(out["brca1"]))
print("ccre cats:", [(r["category"], r["n"]) for r in out["ccre"]])
print("hist n: 7b", len(out["hist"]["d7"]), "40b", len(out["hist"]["d40"]))
db.close()
