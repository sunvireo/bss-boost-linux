"""Opt-in compositor-shortcut bridge, without reading privileged input devices.

Linux desktop users can bind a custom compositor shortcut to:
    /path/to/BssBooster --control start
    /path/to/BssBooster --control pause
    /path/to/BssBooster --control stop
    /path/to/BssBooster --control alarm:Glitter

The running application listens on a per-user Unix socket (0600). A callback
runs on a daemon thread; GUI consumers MUST forward commands to the Qt thread.
"""
from __future__ import annotations

import os
import socket
import tempfile
import threading
from pathlib import Path

ALLOWED = frozenset(('start', 'pause', 'stop'))


def command_is_valid(command: str) -> bool:
    return (command in ALLOWED or
            (command.startswith('alarm:') and 0 < len(command[6:]) <= 70))


def socket_path() -> Path:
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if runtime and Path(runtime).is_dir():
        directory = Path(runtime)
    else:
        directory = Path(tempfile.gettempdir()) / f'bssbooster-{os.getuid()}'
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if directory.is_symlink() or directory.stat().st_uid != os.getuid():
            raise PermissionError('Unsafe IPC directory')
        directory.chmod(0o700)
    return directory / 'bssbooster-control.sock'


def send_control(command: str) -> bool:
    if not command_is_valid(command) or os.name == 'nt':
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            s.connect(str(socket_path()))
            s.sendall((command + '\n').encode('utf-8'))
            return s.recv(32).startswith(b'OK')
    except (OSError, UnicodeError):
        return False


class ControlServer:
    def __init__(self, on_command):
        self.on_command = on_command
        self._sock = None
        self._thread = None
        self._stop = threading.Event()
        self.path = socket_path()
        self._owns_path = False

    def start(self) -> bool:
        if self._sock is not None:
            return True
        path = self.path
        try:
            if path.exists() or path.is_socket():
                if path.is_symlink() or not path.is_socket() or path.stat().st_uid != os.getuid():
                    return False
                # A second running app should never steal a live listener.
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                    probe.settimeout(.25)
                    try:
                        probe.connect(str(path))
                    except (ConnectionRefusedError, FileNotFoundError):
                        path.unlink(missing_ok=True)
                    else:
                        return False
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._sock.settimeout(.25)
            self._sock.bind(str(path))
            path.chmod(0o600)
            self._owns_path = True
            self._sock.listen(4)
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name='BssControl', daemon=True)
            self._thread.start()
            return True
        except OSError:
            if self._sock is not None:
                self._sock.close()
                self._sock = None
            return False

    def _loop(self):
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except (socket.timeout, OSError):
                continue
            with conn:
                try:
                    conn.settimeout(.5)
                    command = conn.recv(512).decode('utf-8').strip()
                    if command_is_valid(command):
                        self.on_command(command)
                        conn.sendall(b'OK\n')
                    else:
                        conn.sendall(b'BAD\n')
                except (OSError, UnicodeError):
                    continue

    def close(self):
        self._stop.set()
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        if self._thread is not None:
            self._thread.join(timeout=.8)
            self._thread = None
        try:
            if self._owns_path and self.path.is_socket() and self.path.stat().st_uid == os.getuid():
                self.path.unlink()
            self._owns_path = False
        except OSError:
            pass
