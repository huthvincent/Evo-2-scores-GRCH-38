#!/usr/bin/env python3
"""Fig3 — each panel as a standalone high-res figure (600 dpi PNG + vector PDF)."""
import json, numpy as np, sqlite3
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

OUT="/Users/rui/Desktop/papers/NAR/database/figures/Fig3"
DB="/Users/rui/Desktop/papers/NAR/database/evo2_database/evo2.db"
D=json.load(open("/Users/rui/Desktop/papers/NAR/database/figures/case_data.json"))
ACCENT="#2563EB"; INK="#0F172A"; MUTED="#475569"; GRID="#E2E8F0"
EVO=LinearSegmentedColormap.from_list("evo_delta",["#A32D2D","#E24B4A","#F09595","#C9CCD6","#97C459","#639922"])
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.edgecolor":"#94A3B8",
                     "axes.linewidth":0.9,"axes.titlesize":13,"axes.titleweight":"bold"})

def save(fig,name):
    fig.tight_layout()
    fig.savefig(f"{OUT}/{name}.png",dpi=600,bbox_inches="tight")
    fig.savefig(f"{OUT}/{name}.pdf",bbox_inches="tight")
    plt.close(fig); print("saved",name)

def boxes(ax,groups,labels,title,nlabels=None):
    data=[np.array(g) for g in groups]; means=[float(np.mean(g)) if len(g) else 0 for g in groups]
    vmax=max(1.0,max(abs(m) for m in means)); norm=TwoSlopeNorm(vcenter=0,vmin=-vmax,vmax=vmax)
    bp=ax.boxplot(data,showfliers=False,patch_artist=True,widths=0.62,medianprops={"color":INK,"linewidth":1.4})
    for patch,m in zip(bp["boxes"],means): patch.set(facecolor=EVO(norm(m)),edgecolor="#334155",linewidth=0.9)
    ax.axhline(0,color=MUTED,lw=0.9,ls="--"); ax.set_yscale("symlog",linthresh=10)
    ax.set_xticks(range(1,len(labels)+1)); ax.set_xticklabels(labels,rotation=25,ha="right",fontsize=10)
    ax.set_ylabel("Evo2-40B Δ score"); ax.set_title(title); ax.grid(axis="y",color=GRID,lw=0.6); ax.set_axisbelow(True)
    if nlabels:
        for i,n in enumerate(nlabels): ax.text(i+1,ax.get_ylim()[1],n,ha="center",va="bottom",fontsize=8,color=MUTED)

# a — Δ by functional region
forder=[f for f in ["exonic","UTR5","UTR3","ncRNA_exonic","upstream","downstream","intronic","ncRNA_intronic","intergenic"] if f in D["delta_by_func"]]
fig,ax=plt.subplots(figsize=(7.2,5.2))
boxes(ax,[D["delta_by_func"][f] for f in forder],[f.replace("ncRNA_","ncRNA ") for f in forder],
      "Δ distribution by functional region",[f"{len(D['delta_by_func'][f])//1000}k" for f in forder])
save(fig,"a_delta_by_functional_region")

# b — Δ by coding consequence
eorder=[e for e in ["synonymous SNV","nonsynonymous SNV","startloss","stoploss","stopgain"] if e in D["delta_by_exonic"]]
fig,ax=plt.subplots(figsize=(6.4,5.2))
boxes(ax,[D["delta_by_exonic"][e] for e in eorder],["synon.","nonsynon.","startloss","stoploss","stopgain"][:len(eorder)],
      "Δ distribution by coding consequence",[f"n={len(D['delta_by_exonic'][e])}" for e in eorder])
save(fig,"b_delta_by_coding_consequence")

# c — Spearman concordance heatmap among the 6 delta scores
dcols=["evo7b_noRC_delta_score","evo7b_avgRC_delta_score","evo7b_weightRC_delta_score",
       "evo40b_noRC_delta_score","evo40b_avgRC_delta_score","evo40b_weightRC_delta_score"]
db=sqlite3.connect(DB)
A=np.array(db.execute(f"SELECT {','.join(dcols)} FROM variants WHERE rowid % 200 = 0").fetchall(),dtype=float); db.close()
R=np.apply_along_axis(lambda c: np.argsort(np.argsort(c)),0,A); M=np.corrcoef(R,rowvar=False)
slab=["7B noRC","7B avgRC","7B wtRC","40B noRC","40B avgRC","40B wtRC"]
fig,ax=plt.subplots(figsize=(6.6,5.6))
im=ax.imshow(M,cmap="Blues",vmin=0.2,vmax=1.0)
ax.set_xticks(range(6)); ax.set_xticklabels(slab,rotation=45,ha="right",fontsize=9)
ax.set_yticks(range(6)); ax.set_yticklabels(slab,fontsize=9)
for i in range(6):
    for j in range(6): ax.text(j,i,f"{M[i,j]:.2f}",ha="center",va="center",fontsize=8.5,color="white" if M[i,j]>0.7 else INK)
cb=plt.colorbar(im,ax=ax,fraction=0.046,pad=0.03); cb.set_label("Spearman ρ",fontsize=9)
ax.set_title("Score concordance: strategies agree, scales differ")
save(fig,"c_score_concordance")

# d — APOE-locus variant landscape
gc=D["gene_case"]; b=gc["rows"]; gname=gc["gene"]; chrom=b[0]["CHR"]
bx=np.array([r_["BP"] for r_ in b])/1e6; bd=np.array([r_["d40"] for r_ in b])
vlim=max(abs(np.percentile(bd,2)),abs(np.percentile(bd,98)),1); norm=TwoSlopeNorm(vcenter=0,vmin=-vlim,vmax=vlim)
fig,ax=plt.subplots(figsize=(7.6,5.2))
sc=ax.scatter(bx,bd,c=bd,cmap=EVO,norm=norm,s=26,edgecolors="#334155",linewidths=0.3)
ax.axhline(0,color=MUTED,lw=0.9,ls="--")
ax.set_xlabel(f"{gname} locus position (chr{chrom}, Mb)"); ax.set_ylabel("Evo2-40B Δ score")
ax.set_title(f"Variant landscape across the {gname} locus (n={len(b)}, common)")
cb=plt.colorbar(sc,ax=ax,fraction=0.046,pad=0.03); cb.set_label("Δ  (disfavored ↔ tolerated)",fontsize=9)
ax.grid(color=GRID,lw=0.6); ax.set_axisbelow(True)
save(fig,"d_apoe_locus_landscape")
print("Fig3 panels done")
