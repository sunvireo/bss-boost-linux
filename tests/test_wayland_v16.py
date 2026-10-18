"""Wayland uinput backend and opt-in compositor shortcut bridge."""
import os
import socket
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from bss_booster import linux_backend as backend
from bss_booster import linux_control as ctrl


def test_wayland_keypresses_use_linux_event_codes_and_do_not_probe_focus(monkeypatch):
    monkeypatch.setattr(backend.os, 'name', 'posix')
    monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')
    monkeypatch.setenv('DISPLAY', ':0')
    monkeypatch.setattr(backend.shutil, 'which', lambda name: f'/usr/bin/{name}')
    calls = []
    def fake_run(args, **kwargs):
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout='Roblox')
    monkeypatch.setattr(backend.subprocess, 'run', fake_run)
    assert backend.wayland_session()
    assert not backend.x11_available()
    assert backend.wayland_available()
    assert backend.linux_backend_ready()
    assert not backend.LinuxKeyboard.focused('Roblox')
    assert calls == []   # No fake foreground claim on Wayland.
    assert backend.LinuxKeyboard.send(1)
    assert backend.LinuxKeyboard.send(7)
    assert calls == [['ydotool', 'key', '2:1', '2:0'],
                     ['ydotool', 'key', '8:1', '8:0']]
    assert not backend.LinuxKeyboard.send(0)
    assert not backend.LinuxKeyboard.send(8)
    assert not backend.LinuxKeyboard.send(True)


def test_wayland_requires_ydotool_and_connected_daemon(monkeypatch):
    monkeypatch.setattr(backend.os, 'name', 'posix')
    monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')
    monkeypatch.setattr(backend.shutil, 'which', lambda _: None)
    assert not backend.linux_backend_ready()
    assert not backend.LinuxKeyboard.send(2)
    monkeypatch.setattr(backend.shutil, 'which', lambda _: '/usr/bin/ydotool')
    monkeypatch.setattr(backend.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=1))
    assert not backend.LinuxKeyboard.send(2)  # no working daemon / socket
    def fail(*args, **kwargs):
        raise FileNotFoundError('ydotool socket missing')
    monkeypatch.setattr(backend.subprocess, 'run', fail)
    assert not backend.LinuxKeyboard.send(2)


def test_x11_still_uses_xdotool_and_wayland_without_session_var(monkeypatch):
    monkeypatch.setattr(backend.os, 'name', 'posix')
    monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
    monkeypatch.setenv('WAYLAND_DISPLAY', 'wayland-0')
    assert backend.wayland_session()
    monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
    monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')
    monkeypatch.setenv('DISPLAY', ':9')
    monkeypatch.setattr(backend.shutil, 'which', lambda _: '/usr/bin/xdotool')
    seen = []
    def fake_run(args, **kwargs):
        seen.append(args)
        return SimpleNamespace(returncode=0, stdout='Roblox')
    monkeypatch.setattr(backend.subprocess, 'run', fake_run)
    assert backend.linux_backend_ready()
    assert backend.LinuxKeyboard.focused('roblox')
    assert backend.LinuxKeyboard.send(2)
    assert seen[-1] == ['xdotool', 'key', '--clearmodifiers', '2']


@pytest.mark.skipif(os.name == 'nt', reason='Unix-domain socket Linux feature')
def test_control_bridge_roundtrip_and_socket_permissions(monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_RUNTIME_DIR', str(tmp_path))
    commands = []
    server = ctrl.ControlServer(commands.append)
    assert server.start()
    try:
        assert server.path.is_socket()
        assert (server.path.stat().st_mode & 0o777) == 0o600
        assert ctrl.send_control('start')
        assert ctrl.send_control('pause')
        assert ctrl.send_control('alarm:Glitter')
        for _ in range(30):
            if len(commands) >= 3:
                break
            time.sleep(.01)
        assert commands == ['start', 'pause', 'alarm:Glitter']
        assert not ctrl.send_control('rm -rf ~')
        assert not ctrl.send_control('alarm:')
        other = ctrl.ControlServer(lambda x: None)
        assert not other.start()
        other.close()
        assert server.path.is_socket()  # second instance must not delete live socket
        assert ctrl.send_control('stop')
    finally:
        server.close()
    assert not server.path.exists()
    assert not ctrl.send_control('start')
