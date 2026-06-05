#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
TMP_DIR="/tmp/context9_pkg_$$"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

rsync -av \
    --exclude='.venv' \
    --exclude='.git' \
    --exclude='.idea' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    "$SCRIPT_DIR/" "$TMP_DIR/"

"$VENV_PYTHON" -m zipapp "$TMP_DIR" -o "$SCRIPT_DIR/.pyz_tmp" -p "$VENV_PYTHON"

mv "$SCRIPT_DIR/.pyz_tmp" "$HOME/.mcp/context9.pyz"

echo "Packaged to $HOME/.mcp/context9.pyz"
