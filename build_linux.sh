#!/usr/bin/env bash
# Build a Linux binary (run this on Linux; not Windows).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
if [[ ! -f .venv/bin/python ]]; then
  python3 -m venv .venv
fi
".venv/bin/python" -m pip install -r requirements-linux.txt 'pyinstaller>=6,<7' pytest
".venv/bin/python" -m pytest -q tests
".venv/bin/python" -m PyInstaller --noconfirm --clean --onefile --windowed \
  --name BssBooster \
  --add-data 'assets/bss_booster_icon.png:assets' \
  --add-data 'assets/booster_alarm.wav:assets' \
  main.py
chmod +x dist/BssBooster
printf '\nBuilt: %s/dist/BssBooster\n' "$PWD"
printf 'Use ./dist/BssBooster to run. X11 + xdotool needed for macro keys.\n'
