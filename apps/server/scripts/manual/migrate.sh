#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Executando migrations..."
python "$ROOT_DIR/scripts/manage_db.py"
echo "Migrations concluidas!"
