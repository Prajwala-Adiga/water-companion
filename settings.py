"""Persistent user preferences and Windows sign-in integration."""
import json
import os
from pathlib import Path
import sys
import time


DEFAULTS = {
    'interval_minutes': 120,
    'snooze_short_minutes': 5,
    'snooze_long_minutes': 10,
    'sound_enabled': False,
    'preferred_monitor': 0,
    'start_with_windows': False,
    'character': 'friendly',
}


class Settings:
    def __init__(self, path: Path):
        self.path = path
        self.values = dict(DEFAULTS)
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                self.values.update({key: data[key] for key in DEFAULTS if key in data})
        except (OSError, ValueError, TypeError):
            pass
        self._validate()

    def _validate(self):
        for key, low, high in (
            ('interval_minutes', 15, 720),
            ('snooze_short_minutes', 1, 60),
            ('snooze_long_minutes', 1, 60),
            ('preferred_monitor', 0, 32),
        ):
            value = self.values[key]
            if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
                self.values[key] = DEFAULTS[key]
        for key in ('sound_enabled', 'start_with_windows'):
            if not isinstance(self.values[key], bool):
                self.values[key] = DEFAULTS[key]
        if self.values['character'] not in ('friendly', 'ranga'):
            self.values['character'] = DEFAULTS['character']

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.values, indent=2), encoding='utf-8')
        for attempt in range(4):
            try:
                os.replace(temp, self.path)
                break
            except PermissionError:
                if attempt == 3:
                    raise
                time.sleep(0.05 * (attempt + 1))

    def __getattr__(self, name):
        if name in self.values:
            return self.values[name]
        raise AttributeError(name)


def startup_command():
    if getattr(sys, 'frozen', False):
        return f'"{Path(sys.executable).resolve()}"'
    pythonw = Path(sys.executable).with_name('pythonw.exe')
    executable = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{executable.resolve()}" "{(Path(__file__).resolve().parent / "app.py")}"'


def set_start_with_windows(enabled):
    if os.name != 'nt':
        return
    import winreg
    key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        if enabled:
            winreg.SetValueEx(key, 'FahadhWaterCompanion', 0, winreg.REG_SZ, startup_command())
        else:
            try:
                winreg.DeleteValue(key, 'FahadhWaterCompanion')
            except FileNotFoundError:
                pass
