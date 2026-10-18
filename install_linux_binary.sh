#!/usr/bin/env bash
# Optional user-only Linux install; run after build_linux.sh or a GitHub Linux artifact.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
if [[ ! -x dist/BssBooster ]]; then
  echo 'Expected dist/BssBooster: build it or copy the executable here.' >&2
  exit 1
fi
mkdir -p "$HOME/.local/opt/BssBooster" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/256x256/apps"
install -m 755 dist/BssBooster "$HOME/.local/opt/BssBooster/BssBooster"
install -m 644 assets/bss_booster_icon.png "$HOME/.local/share/icons/hicolor/256x256/apps/bss-booster.png"
cat > "$HOME/.local/share/applications/bss-booster.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Bss Booster
Comment=Bee Swarm boosting macro and alarm overlays
Exec=$HOME/.local/opt/BssBooster/BssBooster
Icon=bss-booster
Categories=Utility;Game;
Terminal=false
StartupNotify=true
EOF
chmod 644 "$HOME/.local/share/applications/bss-booster.desktop"
echo 'Bss Booster installed for this user. Find it in the application launcher.'
