"""Best-effort desktop controls for Linux X11, with safe failure on Wayland.

No elevated permissions, kernel modules, hidden drivers or screen scraping.
X11 session + xdotool required for sending keys to a focused Roblox window.
"""
from __future__ import annotations

import os
import shutil
import subprocess


def x11_available() -> bool:
    # Avoid claiming Wayland is supported just because XWayland provides DISPLAY.
    # Users should log into an Xorg/X11 session for reliable key injection.
    return (os.name != "nt" and os.environ.get("XDG_SESSION_TYPE", "").lower() != "wayland"
            and bool(os.environ.get("DISPLAY")) and bool(shutil.which("xdotool")))


class LinuxKeyboard:
    """Send keys into the CURRENT focused window only. Never focus other apps."""

    @staticmethod
    def focused(target_title: str) -> bool:
        if not x11_available() or not isinstance(target_title, str) or not target_title.strip():
            return False
        try:
            result = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                                    capture_output=True, text=True, timeout=1.2, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0 and target_title.casefold() in result.stdout.casefold()

    @staticmethod
    def send(key: int) -> bool:
        if not x11_available() or not isinstance(key, int) or not 1 <= key <= 7:
            return False
        try:
            result = subprocess.run(["xdotool", "key", "--clearmodifiers", str(key)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=1.2, check=False)
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False


def keyboard_backend():
    if os.name == "nt":
        from .engine import WindowsKeyboard
        return WindowsKeyboard
    return LinuxKeyboard
