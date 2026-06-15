#!/usr/bin/env python3
"""High-res screenshots of the live Datasette pages for the NAR interface figure."""
from playwright.sync_api import sync_playwright
import os

BASE = "http://127.0.0.1:8765"
OUT = "/Users/rui/Desktop/papers/NAR/database/figures/screens"
os.makedirs(OUT, exist_ok=True)

# (name, path, full_page)
SHOTS = [
    ("landing",    "/",                                          True),
    ("about",      "/about",                                     True),
    ("gene_brca1", "/evo2/gene_top_impact?gene=BRCA1",           False),
    ("faceted",    "/evo2/variants?_facet=Func_ensGene&_facet=ExonicFunc_ensGene", False),
    ("variant",    "/evo2/lookup_by_rsid?rsid=rs76735897",       False),
    ("search",     "/evo2/variants?_search=BRCA1",               False),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    for name, path, full in SHOTS:
        page.goto(BASE + path, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(900)
        page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
        print("shot", name, "->", f"{OUT}/{name}.png")
    browser.close()
print("done")
