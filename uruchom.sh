#!/usr/bin/env sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$project_dir/.venv/bin/python" ]; then
    echo 'Brak .venv. Przygotuj środowisko według README.md lub użyj paczki przenośnej.' >&2
    exit 1
fi
cd "$project_dir"
exec "$project_dir/.venv/bin/python" -m meeting_timer "$@"
