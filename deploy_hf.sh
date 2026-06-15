#!/usr/bin/env bash
# One-shot deploy to HuggingFace. Requires: `hf auth login` already done.
#   Dataset repo  -> holds evo2.parquet (+ evo2.db) + card   (data + HF Viewer + download)
#   Space repo    -> Datasette web app; bakes evo2.db into the image at build time
set -euo pipefail
cd "$(dirname "$0")"
HF="./.venv/bin/hf"

DATASET="huthvincent/Evo2-Variant-DB"     # must match DB_URL ARG in space/Dockerfile
SPACE="huthvincent/evo2-database"

echo "== auth =="; $HF auth whoami

# sync the verified config + front-end into the Space build context
cp metadata.yml space/metadata.yml
rm -rf space/templates space/static && cp -r templates static space/

echo "== [1/4] create dataset repo (public) =="
$HF repo create "$DATASET" --type dataset --public --exist-ok

echo "== [2/4] upload data + card =="
$HF upload "$DATASET" dataset/README.md README.md    --type dataset --commit-message "dataset card"
$HF upload "$DATASET" evo2.parquet      evo2.parquet --type dataset --commit-message "Evo2 scores (parquet)"
echo "   uploading evo2.db (3.4 GB — this is the slow step) ..."
$HF upload "$DATASET" evo2.db           evo2.db      --type dataset --commit-message "Evo2 SQLite for Datasette"

echo "== [3/4] create Space (docker, public) =="
$HF repo create "$SPACE" --type space --space-sdk docker --public --exist-ok

echo "== [4/4] upload Space (triggers build; build bakes in the db from the dataset repo) =="
$HF upload "$SPACE" space/ . --type space --commit-message "Datasette deployment"

echo
echo "DONE."
echo "  Dataset : https://huggingface.co/datasets/$DATASET"
echo "  Space   : https://huggingface.co/spaces/$SPACE   (building now — first build downloads the 3.4GB db)"
