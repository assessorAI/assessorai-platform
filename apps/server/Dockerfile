FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

RUN python -m venv .venv
COPY . ./
RUN .venv/bin/pip install --upgrade pip && .venv/bin/pip install .

FROM python:3.12-slim

RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .
RUN chmod +x /app/scripts/entrypoint.sh

ENTRYPOINT ["bash", "/app/scripts/entrypoint.sh"]
