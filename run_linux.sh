#!/usr/bin/env bash
# Run Bss Booster from source on Linux (Python used only for this source launcher).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
  echo 'WARNING: You are using Wayland. Hotbar macro input and global shortcuts require X11/Xorg.' >&2
fi
if ! command -v xdotool >/dev/null 2>&1; then
  echo 'TIP: Install xdotool for the macro: sudo apt install xdotool' >&2
fi
if ! command -v espeak-ng >/dev/null 2>&1 && ! command -v espeak >/dev/null 2>&1; then
  echo 'TIP: Install espeak-ng for voice alerts: sudo apt install espeak-ng' >&2
fi
if [[ ! -f .venv/bin/python ]]; then
  python3 -m venv .venv
fi
".venv/bin/python" -m pip install -r requirements-linux.txt
exec .venv/bin/python main.py
