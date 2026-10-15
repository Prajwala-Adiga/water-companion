"""Persistent wall-clock scheduling, independent of the GUI."""
import json
import math
from pathlib import Path

INTERVAL = 2 * 60 * 60

class Schedule:
    def __init__(self, path: Path, now: float):
        self.path = path
        self.paused = False
        self.next_due = now + INTERVAL
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            due = float(data['next_due'])
            if not math.isfinite(due):
                raise ValueError('Invalid timestamp')
            self.next_due = due
            self.paused = data.get('paused') is True
        except (OSError, ValueError, KeyError, TypeError):
            pass

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps({'next_due': self.next_due, 'paused': self.paused}), encoding='utf-8')
        temp.replace(self.path)

    def due(self, now):
        return not self.paused and now >= self.next_due

    def postpone(self, now, seconds=INTERVAL):
        self.next_due = now + seconds
        self.save()

    def pause(self, paused, now):
        self.paused = paused
        if not paused:
            self.next_due = now + INTERVAL
        self.save()
