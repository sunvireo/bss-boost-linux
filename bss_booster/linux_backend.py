"""Linux hotbar keys: xdotool on X11; ydotool/uinput on Wayland.

Wayland compositors do not expose a universal foreground-window API. Therefore
focused() deliberately fails closed on Wayland. A user must explicitly disable
the window-title guard in Settings before the macro may send keys there.

We never install/launch a privileged daemon or alter device permissions.
Linux users install and configure ydotoold themselves, then test with their
own compositor. ydotool uses Linux input-event KEY_* codes (not X11 keysyms).
"""
from __future__ import annotations

import os
import shutil
import subprocess


def wayland_session() -> bool:
    if os.name == 'nt':
        return False
    session = os.environ.get('XDG_SESSION_TYPE', '').lower()
    return session == 'wayland' or (not session and bool(os.environ.get('WAYLAND_DISPLAY')))


def x11_available() -> bool:
    return (os.name != 'nt' and not wayland_session()
            and bool(os.environ.get('DISPLAY')) and bool(shutil.which('xdotool')))


def wayland_available() -> bool:
    """ydotool executable is available; daemon/socket access checked on send."""
    return wayland_session() and bool(shutil.which('ydotool'))


def linux_backend_ready() -> bool:
    return wayland_available() if wayland_session() else x11_available()


def linux_backend_label() -> str:
    if wayland_session():
        return 'Wayland (ydotool)' if wayland_available() else 'Wayland (ydotool not installed)'
    return 'X11 (xdotool)' if x11_available() else 'X11 (xdotool or DISPLAY unavailable)'


class LinuxKeyboard:
    """Issue a configured hotbar number. Never change focus or window selection."""

    @staticmethod
    def focused(target_title: str) -> bool:
        # There is no compositor-independent active-window title check on Wayland.
        if wayland_session() or not x11_available() or not isinstance(target_title, str) or not target_title.strip():
            return False
        try:
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'],
                                    capture_output=True, text=True, timeout=1.2, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0 and target_title.casefold() in result.stdout.casefold()

    @staticmethod
    def send(key: int) -> bool:
        if not isinstance(key, int) or isinstance(key, bool) or not 1 <= key <= 7:
            return False
        try:
            if wayland_session():
                if not wayland_available():
                    return False
                # Linux input-event KEY_1 == 2, KEY_2 == 3 ... KEY_7 == 8.
                code = key + 1
                argv = ['ydotool', 'key', f'{code}:1', f'{code}:0']
            else:
                if not x11_available():
                    return False
                argv = ['xdotool', 'key', '--clearmodifiers', str(key)]
            result = subprocess.run(argv, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=1.5, check=False)
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False


def keyboard_backend():
    if os.name == 'nt':
        from .engine import WindowsKeyboard
        return WindowsKeyboard
    return LinuxKeyboard
