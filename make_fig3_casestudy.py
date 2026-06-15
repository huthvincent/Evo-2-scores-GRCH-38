#!/usr/bin/env python3
"""Figure 3 — data analysis + BRCA1 case study (4 panels)."""
import json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

D = json.load(open("/Users/rui/Desktop/papers/NAR/database/figures/case_data.json"))
ACCENT="#2563EB"; INK="#0F172A"; MUTED="#475569"; GRID="#E2E8F0"
EVO = LinearSegmentedColormap.from_list("evo_delta", ["#A32D2D","#E24B4A","#F09595","#C9CCD6","#97C459","#639922"])
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.edgecolor":"#94A3B8",
                     "axes.linewidth":0.8,"axes.titlesize":11,"axes.titleweight":"bold"})

def letter(ax,s): ax.text(-0.14,1.05,s,transform=ax.transAxes,fontsize=14,fontweight="bold",color=INK,va="top")
def spearman(a,b):
    ra=np.argsort(np.argsort(a)); rb=np.argsort(np.argsort(b)); return np.corrcoef(ra,rb)[0,1]

def boxes(ax, groups, labels, title, ylab="Evo2-40B Δ score"):
    data=[np.array(g) for g in groups]; means=[float(np.mean(g)) if len(g) else 0 for g in groups]
    vmax=max(1.0, max(abs(m) for m in means)); norm=TwoSlopeNorm(vcenter=0, vmin=-vmax, vmax=vmax)
    bp=ax.boxplot(data, showfliers=False, patch_artist=True, widths=0.62,
                  medianprops={"color":INK,"linewidth":1.3})
    for patch,m in zip(bp["boxes"],means):
        patch.set(facecolor=EVO(norm(m)), edgecolor="#334155", linewidth=0.8)
    ax.axhline(0,color=MUTED,lw=0.8,ls="--"); ax.set_yscale("symlog",linthresh=10)
    ax.set_xticks(range(1,len(labels)+1)); ax.set_xticklabels(labels,rotation=25,ha="right",fontsize=8.5)
    ax.set_ylabel(ylab); ax.set_title(title); ax.grid(axis="y",color=GRID,lw=0.6); ax.set_axisbelow(True)
    return means

fig,axs=plt.subplots(2,2,figsize=(12,9.4))

# A. delta by functional region
ax=axs[0,0]
forder=["exonic","UTR5","UTR3","ncRNA_exonic","upstream","downstream","intronic","ncRNA_intronic","intergenic"]
forder=[f for f in forder if f in D["delta_by_func"]]
flab=[f.replace("ncRNA_","ncRNA ") for f in forder]
boxes(ax,[D["delta_by_func"][f] for f in forder],flab,"Δ distribution by functional region")
for i,f in enumerate(forder):
    ax.text(i+1, ax.get_ylim()[1], f"{len(D['delta_by_func'][f])//1000}k", ha="center",va="bottom",fontsize=6.5,color=MUTED)
letter(ax,"a")

# B. delta by coding consequence
ax=axs[0,1]
eorder=["synonymous SNV","nonsynonymous SNV","startloss","stoploss","stopgain"]
eorder=[e for e in eorder if e in D["delta_by_exonic"]]
elab=["synon.","nonsynon.","startloss","stoploss","stopgain"][:len(eorder)]
boxes(ax,[D["delta_by_exonic"][e] for e in eorder],elab,"Δ distribution by coding consequence")
for i,e in enumerate(eorder):
    ax.text(i+1, ax.get_ylim()[1], f"n={len(D['delta_by_exonic'][e])}", ha="center",va="bottom",fontsize=6.5,color=MUTED)
letter(ax,"b")

# C. Spearman concordance among all 6 delta scores (model x strand strategy)
ax=axs[1,0]
import sqlite3
dcols=["evo7b_noRC_delta_score","evo7b_avgRC_delta_score","evo7b_weightRC_delta_score",
       "evo40b_noRC_delta_score","evo40b_avgRC_delta_score","evo40b_weightRC_delta_score"]
_db=sqlite3.connect("/Users/rui/Desktop/papers/NAR/database/evo2_database/evo2.db")
_A=np.array(_db.execute(f"SELECT {','.join(dcols)} FROM variants WHERE rowid % 200 = 0").fetchall(),dtype=float)
_db.close()
_R=np.apply_along_axis(lambda c: np.argsort(np.argsort(c)),0,_A)
M=np.corrcoef(_R,rowvar=False)
slab=["7B noRC","7B avgRC","7B wtRC","40B noRC","40B avgRC","40B wtRC"]
im=ax.imshow(M,cmap="Blues",vmin=0.2,vmax=1.0)
ax.set_xticks(range(6)); ax.set_xticklabels(slab,rotation=45,ha="right",fontsize=8)
ax.set_yticks(range(6)); ax.set_yticklabels(slab,fontsize=8)
for i in range(6):
    for j in range(6):
        ax.text(j,i,f"{M[i,j]:.2f}",ha="center",va="center",fontsize=7.5,
                color="white" if M[i,j]>0.7 else INK)
cb=plt.colorbar(im,ax=ax,fraction=0.046,pad=0.03); cb.set_label("Spearman ρ",fontsize=8)
ax.set_title("Score concordance: strategies agree, scales differ")
letter(ax,"c")

# D. gene case-study variant landscape (FTO — common, mostly noncoding)
ax=axs[1,1]
gc=D["gene_case"]; b=gc["rows"]; gname=gc["gene"]; chrom=b[0]["CHR"]
bx=np.array([r_["BP"] for r_ in b])/1e6; bd=np.array([r_["d40"] for r_ in b])
vlim=max(abs(np.percentile(bd,2)),abs(np.percentile(bd,98)),1); norm=TwoSlopeNorm(vcenter=0,vmin=-vlim,vmax=vlim)
sc=ax.scatter(bx,bd,c=bd,cmap=EVO,norm=norm,s=22,edgecolors="#334155",linewidths=0.25)
ax.axhline(0,color=MUTED,lw=0.8,ls="--")
ax.set_xlabel(f"{gname} locus position (chr{chrom}, Mb)"); ax.set_ylabel("Evo2-40B Δ score")
ax.set_title(f"Variant landscape across the {gname} locus (n={len(b)}, common)")
cb=plt.colorbar(sc,ax=ax,fraction=0.046,pad=0.03); cb.set_label("Δ  (disfavored ↔ tolerated)",fontsize=8)
ax.grid(color=GRID,lw=0.6); ax.set_axisbelow(True); letter(ax,"d")

plt.tight_layout(w_pad=2.6,h_pad=3.2)
for ext,kw in [("pdf",{}),("png",{"dpi":300})]:
    fig.savefig(f"/Users/rui/Desktop/papers/NAR/database/figures/Fig3_casestudy.{ext}",bbox_inches="tight",**kw)
print(f"Fig3 saved. cross-scale 7B-40B noRC rho={M[0,3]:.2f}; within-7B noRC-avgRC rho={M[0,1]:.2f}")
