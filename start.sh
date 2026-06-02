#!/usr/bin/env bash
set -euo pipefail

# Railpack start script — enters the project subdirectory, installs deps, and runs gunicorn
cd "$(dirname "$0")/cctrix-main" || exit 1

echo "Starting build and run from: $(pwd)"

# Upgrade pip and install requirements
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

# Export default PORT if not set
: ${PORT:=5000}

echo "Launching gunicorn on :${PORT}"
exec gunicorn app:app --bind 0.0.0.0:${PORT}
