"""Offline alarm sounds and speech on Linux (no cloud service).

Uses the system's espeak-ng/espeak for voice, and paplay/aplay/ffplay
for repeating chimes. Alarms remain active until acknowledged even if hidden.
"""
from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path


class AlarmNotifier:
    def __init__(self, sound_path: Path):
        self.sound_path = Path(sound_path)
        self.active: dict[str, dict] = {}
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._process_voice = None
        self._process_voice_id = None
        self._process_sound = None
        self._voice_unavailable = False
        self._voice_thread = threading.Thread(target=self._voice_loop, daemon=True, name="BssLinuxVoice")
        self._sound_thread = threading.Thread(target=self._sound_loop, daemon=True, name="BssLinuxSound")
        self._voice_thread.start()
        self._sound_thread.start()

    def trigger(self, alarm: dict):
        if alarm.get("alert_mode") not in ("Voice", "Sound"):
            return
        with self._lock:
            self.active[alarm["id"]] = {"name": alarm["name"], "alert_mode": alarm["alert_mode"]}
        self._wake.set()

    def acknowledge(self, alarm_id: str):
        with self._lock:
            self.active.pop(alarm_id, None)
            if self._process_voice_id == alarm_id and self._process_voice is not None:
                try:
                    self._process_voice.terminate()
                except OSError:
                    pass
            self._stop_sound_if_not_needed()
        self._wake.set()

    def sync(self, alarms: list[dict]):
        enabled = {a["id"]: a for a in alarms if a.get("enabled")}
        with self._lock:
            for aid in list(self.active):
                alarm = enabled.get(aid)
                if alarm is None or alarm.get("alert_mode") not in ("Sound", "Voice"):
                    self.active.pop(aid, None)
                else:
                    self.active[aid] = {"name": alarm["name"], "alert_mode": alarm["alert_mode"]}
            if (self._process_voice_id not in self.active or
                    self.active.get(self._process_voice_id, {}).get("alert_mode") != "Voice"):
                if self._process_voice is not None:
                    try:
                        self._process_voice.terminate()
                    except OSError:
                        pass
            self._stop_sound_if_not_needed()
        self._wake.set()

    def is_alerting(self, aid: str) -> bool:
        with self._lock:
            return aid in self.active

    def _sound_needed(self):
        return any(a["alert_mode"] == "Sound" or
                   (a["alert_mode"] == "Voice" and self._voice_unavailable)
                   for a in self.active.values())

    def _stop_sound_if_not_needed(self):
        if not self._sound_needed() and self._process_sound is not None:
            try:
                self._process_sound.terminate()
            except OSError:
                pass

    def _player_command(self):
        if shutil.which("paplay"):
            return ["paplay", str(self.sound_path)]
        if shutil.which("aplay"):
            return ["aplay", "-q", str(self.sound_path)]
        if shutil.which("ffplay"):
            return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(self.sound_path)]
        return None

    def _sound_loop(self):
        while not self._stop.is_set():
            with self._lock:
                needed = self._sound_needed()
            if not needed:
                self._wake.wait(.4)
                self._wake.clear()
                continue
            command = self._player_command()
            if not command or not self.sound_path.exists():
                self._stop.wait(1)
                continue
            try:
                proc = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                self._stop.wait(1)
                continue
            with self._lock:
                self._process_sound = proc
                if not self._sound_needed() or self._stop.is_set():
                    proc.terminate()
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            finally:
                with self._lock:
                    if self._process_sound is proc:
                        self._process_sound = None
            self._stop.wait(.15)

    def _speak(self, aid: str, name: str):
        voice = shutil.which("espeak-ng") or shutil.which("espeak")
        if not voice:
            with self._lock:
                self._voice_unavailable = True
            self._wake.set()
            self._stop.wait(.8)
            return
        try:
            # Pass alarm text as a single argument, NEVER through a shell.
            proc = subprocess.Popen([voice, "-s", "155", "--", name],
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        except OSError:
            with self._lock:
                self._voice_unavailable = True
            self._wake.set()
            self._stop.wait(.8)
            return
        with self._lock:
            self._process_voice = proc
            self._process_voice_id = aid
            if aid not in self.active or self._stop.is_set():
                proc.terminate()
        try:
            proc.wait(timeout=35)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        finally:
            with self._lock:
                if self._process_voice is proc:
                    self._process_voice = None
                    self._process_voice_id = None

    def _voice_loop(self):
        while not self._stop.is_set():
            with self._lock:
                voices = [(aid, data["name"]) for aid, data in self.active.items()
                          if data["alert_mode"] == "Voice"]
            if not voices or self._voice_unavailable:
                self._wake.wait(.4)
                self._wake.clear()
                continue
            for aid, name in voices:
                if self._stop.is_set():
                    return
                with self._lock:
                    data = self.active.get(aid)
                    if not data or data["alert_mode"] != "Voice":
                        continue
                    name = data["name"]
                self._speak(aid, name)
                if self._stop.wait(.35):
                    return

    def close(self):
        self._stop.set()
        self._wake.set()
        with self._lock:
            self.active.clear()
            for proc in (self._process_voice, self._process_sound):
                if proc is not None:
                    try:
                        proc.terminate()
                    except OSError:
                        pass
        self._voice_thread.join(timeout=1.5)
        self._sound_thread.join(timeout=1.5)
