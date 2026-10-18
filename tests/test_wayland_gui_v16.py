"""Offscreen GUI regression: Wayland guidance, backend guard, shortcut bridge."""
import os
from pathlib import Path
import pytest

pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QLabel
from bss_booster.config import Store, make_alarm
from bss_booster.ui import BoosterWindow


@pytest.mark.skipif(os.name == 'nt', reason='Linux Wayland only')
def test_wayland_ui_shows_safety_notice_and_alarm_bridge(monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')
    monkeypatch.setenv('XDG_RUNTIME_DIR', str(tmp_path))
    app = QApplication.instance() or QApplication([])
    root = Path(__file__).resolve().parents[1]
    store = Store(tmp_path / 'config.json')
    win = BoosterWindow(store, root / 'assets' / 'bss_booster_icon.png')
    try:
        assert win._linux_control is not None
        assert win._linux_control.path.is_socket()
        win.show_page('Settings')
        texts = [w.text() for w in win.centralWidget().findChildren(QLabel)]
        assert any('WAYLAND:' in text for text in texts)
        assert any('ydotool' in text for text in texts)
        alarm = make_alarm('Glitter', 30)
        store.profile['alarms'].append(alarm)
        win.clock.configure(store.profile['alarms'])
        win._run_linux_control('alarm:Glitter')
        assert win.clock.time_left(alarm['id']) > 0
        win._run_linux_control('stop')
        assert not win.scheduler.running
    finally:
        win.close()
        app.processEvents()
