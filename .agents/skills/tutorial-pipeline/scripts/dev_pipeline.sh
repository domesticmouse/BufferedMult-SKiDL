#!/usr/bin/env bash
# Local development pipeline helper for the tutorial Markdown-to-HTML build.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN=".venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

ACTION="${1:-build}"

case "$ACTION" in
  build)
    echo "==> Building tutorial HTML in-place and running validation checks..."
    "$PYTHON_BIN" tutorial/build.py --check
    if command -v ruff >/dev/null 2>&1; then
      echo "==> Linting tutorial/build.py with ruff..."
      ruff check tutorial/build.py
    fi
    ;;

  stage)
    OUT_DIR="${2:-_site}"
    echo "==> Staging clean GitHub Pages artifact into ${OUT_DIR}/..."
    "$PYTHON_BIN" tutorial/build.py --out-dir "$OUT_DIR" --check
    echo "==> Staged files in ${OUT_DIR}/:"
    ls -la "$OUT_DIR" "$OUT_DIR/lessons" "$OUT_DIR/reference"
    ;;

  serve)
    PORT="${2:-8000}"
    echo "==> Building tutorial HTML in-place with validation..."
    "$PYTHON_BIN" tutorial/build.py --check
    echo "==> Serving tutorial at http://127.0.0.1:${PORT}/index.html (Ctrl+C to stop)..."
    exec "$PYTHON_BIN" -m http.server "$PORT" --bind 127.0.0.1 --directory tutorial
    ;;

  clean)
    echo "==> Cleaning generated HTML files and _site/..."
    rm -f tutorial/index.html tutorial/lessons/*.html tutorial/reference/*.html
    rm -rf _site
    echo "✓ Cleaned generated tutorial HTML files."
    ;;

  *)
    echo "Usage: $0 {build|stage [OUT_DIR]|serve [PORT]|clean}" >&2
    exit 1
    ;;
esac
