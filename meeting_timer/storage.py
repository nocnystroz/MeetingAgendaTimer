"""Atomic files in the user's data directory; no secrets in meeting data."""

import json
import math
import os
import sys
import tempfile
from pathlib import Path

from .model import Meeting


def data_directory():
    if override := os.environ.get("MEETING_TIMER_DATA_DIR"):
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "licznik-spotkaniowy"


def atomic_json(path: Path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".save-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def read_json(path):
    if Path(path).stat().st_size > 20 * 1024 * 1024:
        raise ValueError("Plik danych przekracza limit 20 MiB.")
    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("Nieprawidłowa liczba w pliku danych.")
        return result
    def invalid(value):
        raise ValueError("Nieprawidłowa stała w pliku danych.")
    with open(path, encoding="utf-8") as stream:
        return json.load(stream, parse_float=number, parse_constant=invalid)


def save_meeting(path, meeting):
    atomic_json(Path(path), meeting.to_dict())


def load_meeting(path):
    return Meeting.from_dict(read_json(path))


def template_data(meeting, include_notes=False):
    items = []
    for item in meeting.items:
        items.append({"title": item.title, "seconds": item.seconds,
                      "scheduled": item.scheduled,
                      "notes": item.notes if include_notes else ""})
    return Meeting.from_dict({"version": 1, "items": items}).to_dict()
