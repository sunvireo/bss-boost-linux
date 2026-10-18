"""Linux X11 focus guard and keypress backend: no live game/window required."""
from types import SimpleNamespace

from bss_booster import linux_backend as backend


def test_wayland_disables_xdotool_even_if_display_is_set(monkeypatch):
    monkeypatch.setattr(backend.os, "name", "posix")
    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr(backend.shutil, "which", lambda cmd: "/usr/bin/xdotool")
    assert not backend.x11_available()
    assert not backend.LinuxKeyboard.send(2)
    assert not backend.LinuxKeyboard.focused("Roblox")


def test_missing_display_disables_injection(monkeypatch):
    monkeypatch.setattr(backend.os, "name", "posix")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert not backend.x11_available()
    assert not backend.LinuxKeyboard.send(2)


def test_x11_focus_guard_and_macro_keypress(monkeypatch):
    monkeypatch.setattr(backend.os, "name", "posix")
    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setattr(backend.shutil, "which", lambda cmd: "/usr/bin/xdotool")
    sent = []

    def fake_run(argv, **kwargs):
        sent.append(argv)
        return SimpleNamespace(returncode=0, stdout="Sober | Roblox Game")

    monkeypatch.setattr(backend.subprocess, "run", fake_run)
    assert backend.LinuxKeyboard.focused("roblox")
    assert not backend.LinuxKeyboard.focused("")
    assert backend.LinuxKeyboard.send(4)
    assert sent[-1] == ["xdotool", "key", "--clearmodifiers", "4"]
    assert not backend.LinuxKeyboard.send(8)
    assert not backend.LinuxKeyboard.send("4")


def test_x11_errors_do_not_crash_macro(monkeypatch):
    monkeypatch.setattr(backend.os, "name", "posix")
    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setattr(backend.shutil, "which", lambda cmd: "/usr/bin/xdotool")

    def fail(*args, **kwargs):
        raise OSError("no X server")

    monkeypatch.setattr(backend.subprocess, "run", fail)
    assert not backend.LinuxKeyboard.focused("Roblox")
    assert not backend.LinuxKeyboard.send(2)
