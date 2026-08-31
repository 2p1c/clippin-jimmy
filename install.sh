#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/2p1c/clippin-jimmy.git"
INSTALL_DIR="${CLIPPIN_HOME:-$HOME/.clippin-jimmy}"
BIN_DIR="${CLIPPIN_BIN:-$HOME/.local/bin}"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少命令: $1" >&2
    exit 1
  fi
}

pick_python() {
  local cmd
  for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  echo "需要 Python 3.10 或更高版本" >&2
  exit 1
}

need git
PYTHON="$(pick_python)"

mkdir -p "$INSTALL_DIR"
if [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" fetch --depth 1 origin main
  git -C "$INSTALL_DIR" checkout -q main
  git -C "$INSTALL_DIR" reset --hard origin/main
else
  rm -rf "$INSTALL_DIR"
  git clone --depth 1 --branch main "$REPO_URL" "$INSTALL_DIR"
fi

"$PYTHON" -m venv "$INSTALL_DIR/.venv"
# shellcheck disable=SC1091
. "$INSTALL_DIR/.venv/bin/activate"
python -m pip install -U pip
python -m pip install "$INSTALL_DIR"

mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/.venv/bin/jimmy" "$BIN_DIR/jimmy"
ln -sf "$INSTALL_DIR/.venv/bin/clippin-jimmy" "$BIN_DIR/clippin-jimmy"

echo
echo "安装完成。"
echo "请确认 $BIN_DIR 在 PATH 中，例如："
echo "  export PATH=\"$BIN_DIR:\$PATH\""
echo
echo "启动中继:  clippin-jimmy"
echo "启动客户端: jimmy --cheat http://127.0.0.1:8000 --room 口令 --name 显示名"
