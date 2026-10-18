"""Linux X11 global keys via pynput. Keys are NOT grabbed or consumed.

Callbacks are delivered to Qt through signals so widgets are never updated
on the background keyboard-listener thread. On Wayland, safely disable.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from .hotkey_codec import normalize_hotkey
from .linux_backend import x11_available


class LinuxHotkeys(QObject):
    macro_signal = Signal(str)
    alarm_signal = Signal(str)

    def __init__(self, handler, alarm_handler):
        super().__init__()
        self.macro_signal.connect(handler)
        self.alarm_signal.connect(alarm_handler)
        self.registered = []
        self.alarms = {}
        self.failures = []
        self._listener = None
        self._held = set()
        self._fired = set()
        self._bindings = {}

    def register(self, alarms: list[dict]):
        self.unregister()
        if not x11_available():
            self.failures.append("Linux global shortcuts require X11 and xdotool (Wayland unsupported)")
            return
        try:
            from pynput import keyboard
        except (ImportError, RuntimeError, OSError) as exc:
            self.failures.append(f"Global shortcuts unavailable: {type(exc).__name__}")
            return
        self._bindings = {"f1": ("macro", "start"),
                          "f2": ("macro", "pause"), "f3": ("macro", "stop")}
        seen = set(self._bindings)
        for alarm in alarms:
            if not alarm.get("enabled"):
                continue
            shortcut = normalize_hotkey(alarm.get("keybind", ""))
            if not shortcut:
                continue
            canonical = shortcut.casefold().replace("control", "ctrl").replace("meta", "win")
            keys = [x.strip() for x in canonical.split("+")]
            mods = [x for x in ("ctrl", "alt", "shift", "win") if x in keys]
            base = next((x for x in keys if x not in ("ctrl", "alt", "shift", "win")), "")
            identifier = "+".join(sorted(mods) + [base])
            if identifier in seen or not base:
                self.failures.append(alarm["name"] + " (duplicate shortcut)")
            else:
                self._bindings[identifier] = ("alarm", alarm["id"])
                seen.add(identifier)
        try:
            self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self._listener.start()
        except (RuntimeError, OSError) as exc:
            self._listener = None
            self.failures.append(f"X11 global shortcuts unavailable: {type(exc).__name__}")

    @staticmethod
    def _name(key):
        name = getattr(key, "name", None)
        if name is None:
            name = getattr(key, "char", None)
        if not name:
            return ""
        name = str(name).lower()
        names = {"ctrl_l": "ctrl", "ctrl_r": "ctrl", "alt_l": "alt", "alt_r": "alt",
                 "alt_gr": "alt", "shift_l": "shift", "shift_r": "shift",
                 "cmd": "win", "cmd_l": "win", "cmd_r": "win",
                 "page_up": "pgup", "page_down": "pgdown",
                 "return": "enter", "esc": "esc"}
        if len(name) == 1 and ord(name) < 27:
            return chr(ord(name) + 96) if ord(name) > 0 else ""
        return names.get(name, name)

    def _on_press(self, key):
        key_name = self._name(key)
        if not key_name or key_name in self._held:
            return
        self._held.add(key_name)
        if key_name in ("ctrl", "alt", "shift", "win"):
            return
        mods = sorted(self._held.intersection({"ctrl", "alt", "shift", "win"}))
        chord = "+".join(mods + [key_name])
        binding = self._bindings.get(chord)
        if binding:
            kind, value = binding
            if kind == "macro":
                self.macro_signal.emit(value)
            else:
                self.alarm_signal.emit(value)

    def _on_release(self, key):
        self._held.discard(self._name(key))

    def unregister(self):
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._held.clear()
        self._bindings.clear()
        self.registered.clear()
        self.alarms.clear()
