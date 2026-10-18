#!/usr/bin/env bash
# Run Bss Booster from source on Linux (Python used only for this source launcher).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
  echo 'WAYLAND: install ydotool and configure its ydotoold daemon for macro input.' >&2
  echo '  Focus-title detection is unavailable: macros stay blocked until you explicitly disable focus protection in Settings.' >&2
  echo '  For global shortcuts, bind desktop shortcuts to the --control commands in START_LINUX_HERE.md.' >&2
  if ! command -v ydotool >/dev/null 2>&1; then
    echo 'TIP: sudo apt install ydotool (then configure ydotoold)' >&2
  fi
elif ! command -v xdotool >/dev/null 2>&1; then
  echo 'TIP: install xdotool for X11 hotbar macros.' >&2
fi
if ! command -v espeak-ng >/dev/null 2>&1 && ! command -v espeak >/dev/null 2>&1; then
  echo 'TIP: Install espeak-ng for voice alerts: sudo apt install espeak-ng' >&2
fi
if [[ ! -f .venv/bin/python ]]; then
  python3 -m venv .venv
fi
".venv/bin/python" -m pip install -r requirements-linux.txt
exec .venv/bin/python main.py
