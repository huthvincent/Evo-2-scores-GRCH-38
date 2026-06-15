# Datasette server for the Evo2 Variant Effect Database, packaged for a
# HuggingFace Docker Space (or any container host). Listens on $PORT (7860).
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "datasette==0.65.2"

WORKDIR /app
COPY metadata.yml entrypoint.sh ./
COPY templates/ ./templates/
COPY static/ ./static/
RUN chmod +x entrypoint.sh

# Bake the database into the image at build time (fast, reliable cold starts —
# no 3.4 GB re-download when the Space wakes). Pulls from the public dataset repo.
ARG DB_URL="https://huggingface.co/datasets/huthvincent/Evo2-Variant-DB/resolve/main/evo2.db"
RUN wget -q -O /app/evo2.db "$DB_URL" && echo "baked db: $(du -h /app/evo2.db | cut -f1)"

ENV PORT=7860
EXPOSE 7860
CMD ["./entrypoint.sh"]
