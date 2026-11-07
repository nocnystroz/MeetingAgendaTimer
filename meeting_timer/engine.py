"""Deterministic timeline; UI refreshes never determine the flow of time."""

import time
from dataclasses import dataclass

from .model import Item


@dataclass(frozen=True)
class Snapshot:
    index: int
    remaining: float
    state: str
    progress: float
    paused: bool = False


class TimerEngine:
    def __init__(self, items: list[Item], clock=time.monotonic, wall=time.time):
        self.items = items
        self.clock, self.wall = clock, wall
        self.gaps = {}
        for previous, item in zip(items, items[1:]):
            if previous.scheduled is not None and item.scheduled is not None:
                self.gaps[item.id] = max(0, item.scheduled - previous.scheduled - previous.seconds)
        self.started = self.paused = False
        self.completed = False
        self.auto = True
        self.origin = 0.0
        self.anchor = clock()
        self.current_id = items[0].id if items else ""
        self.baseline_end = None

    def slots(self):
        offset, result = 0, []
        for i, item in enumerate(self.items):
            if i:
                offset += self.gaps.get(item.id, 0)
            result.append((offset, offset + item.seconds))
            offset += item.seconds
        return result

    @property
    def total(self):
        slots = self.slots()
        return slots[-1][1] if slots else 0

    @property
    def cursor(self):
        return self.origin + (self.clock() - self.anchor if self.started and not self.paused else 0)

    def seek(self, position):
        self.origin, self.anchor = position, self.clock()

    def start(self, scheduled_epoch=None):
        if not self.items:
            return
        self.started, self.paused = True, False
        self.completed = False
        self.seek(0 if scheduled_epoch is None else self.wall() - scheduled_epoch)
        self.baseline_end = (self.wall() if scheduled_epoch is None else scheduled_epoch) + self.total
        self.current_id = self.items[0].id
        self.snapshot(force=True)

    def toggle_pause(self):
        if not self.started:
            return
        position = self.cursor
        self.paused = not self.paused
        self.seek(position)

    def snapshot(self, force=False):
        if not self.items:
            return Snapshot(-1, 0, "empty", 0, self.paused)
        if self.completed:
            return Snapshot(len(self.items) - 1, 0, "finished", 1, self.paused)
        slots, position = self.slots(), self.cursor
        index = next((i for i, item in enumerate(self.items) if item.id == self.current_id), 0)
        if not self.started:
            return Snapshot(index, self.items[index].seconds, "ready", 0)
        if self.auto or force:
            index = next((i for i, (_, end) in enumerate(slots) if position < end), len(slots))
            if index == len(slots):
                self.current_id = self.items[-1].id
                return Snapshot(len(slots) - 1, 0, "finished", 1, self.paused)
            self.current_id = self.items[index].id
        start, end = slots[index]
        if position < start:
            return Snapshot(index, start - position, "waiting", 0, self.paused)
        remaining = end - position
        return Snapshot(index, remaining, "running" if remaining > 0 else "overtime",
                        min(1, max(0, (position - start) / (end - start))), self.paused)

    def jump(self, index):
        if self.started and self.items and index == len(self.items):
            self.completed = True
            self.current_id = self.items[-1].id
            self.seek(self.total)
            return
        if not 0 <= index < len(self.items):
            return
        self.completed = False
        self.current_id = self.items[index].id
        self.seek(self.slots()[index][0])

    def add_time(self, seconds):
        snap = self.snapshot()
        if snap.index >= 0:
            item = self.items[snap.index]
            item.seconds = max(1, min(604800, item.seconds + seconds))

    def mutate(self, operation):
        """Preserve elapsed time within current item when the preceding plan changes."""
        snap = self.snapshot()
        old_start = self.slots()[snap.index][0] if snap.index >= 0 else 0
        position, current_id = self.cursor, self.current_id
        operation()
        index = next((i for i, item in enumerate(self.items) if item.id == current_id), None)
        if index is not None:
            self.seek(self.slots()[index][0] + position - old_start)

    @property
    def predicted_end(self):
        return self.wall() + max(0, self.total - self.cursor)


def format_time(seconds):
    import math
    count = math.ceil(abs(seconds))
    h, rest = divmod(count, 3600)
    m, s = divmod(rest, 60)
    text = f"{h}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"
    return ("+" if seconds < 0 else "") + text
