"""Entry point. Native Linux desktop shortcuts can send --control commands."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resource(path: str) -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / path


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == '--control' and os.name != 'nt':
        from bss_booster.linux_control import send_control
        command = ' '.join(sys.argv[2:])
        if send_control(command):
            print('Command sent to Bss Booster')
            return 0
        print('No running Bss Booster instance accepted this command.', file=sys.stderr)
        return 1

    # On a Wayland session with XWayland, use Qt's XCB window backend by default.
    # This improves independent overlay positioning on many compositors, but
    # still cannot guarantee stacking above native Wayland fullscreen windows.
    # User choice in QT_QPA_PLATFORM always wins. ydotool remains the input path.
    from bss_booster.linux_backend import wayland_session
    if wayland_session() and os.environ.get('DISPLAY'):
        os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    from bss_booster.config import Store
    from bss_booster.ui import BoosterWindow
    app = QApplication(sys.argv)
    app.setApplicationName('Bss Booster')
    app.setOrganizationName('BssBooster')
    app.setStyle('Fusion')
    icon = resource('assets/bss_booster_icon.png')
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    win = BoosterWindow(Store(), icon)
    win.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
