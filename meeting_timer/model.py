"""Plain data shared by the parser, clock, storage and UI. No Qt dependency."""

import math
from dataclasses import asdict, dataclass, field
from uuid import uuid4


@dataclass
class Task:
    text: str = ""
    owner: str = ""
    due: str = ""
    done: bool = False


@dataclass
class Item:
    title: str
    seconds: int
    scheduled: int | None = None
    id: str = field(default_factory=lambda: uuid4().hex)
    notes: str = ""
    decisions: str = ""
    tasks: list[Task] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Nieprawidłowy punkt agendy.")
        if not isinstance(data.get("title"), str) or not data["title"].strip():
            raise ValueError("Brak tytułu punktu.")
        seconds = data.get("seconds")
        if type(seconds) is not int or not 1 <= seconds <= 604800:
            raise ValueError("Nieprawidłowy czas punktu.")
        scheduled = data.get("scheduled")
        if scheduled is not None and (type(scheduled) is not int or scheduled < 0):
            raise ValueError("Nieprawidłowa godzina.")
        for key in ("id", "notes", "decisions"):
            if not isinstance(data.get(key, ""), str):
                raise ValueError("Nieprawidłowe dane punktu.")
        tasks = []
        for task in data.get("tasks", []):
            if not isinstance(task, dict) or any(
                not isinstance(task.get(k, ""), str) for k in ("text", "owner", "due")
            ) or type(task.get("done", False)) is not bool:
                raise ValueError("Nieprawidłowe zadanie.")
            tasks.append(Task(**{k: task[k] for k in ("text", "owner", "due", "done") if k in task}))
        return cls(data["title"], seconds, scheduled, data.get("id") or uuid4().hex,
                   data.get("notes", ""), data.get("decisions", ""), tasks)


@dataclass
class Meeting:
    items: list[Item] = field(default_factory=list)
    removed: list[Item] = field(default_factory=list)
    recordings: list[dict] = field(default_factory=list)
    transcripts: list[dict] = field(default_factory=list)
    screenshots: list[dict] = field(default_factory=list)

    def to_dict(self):
        return {"version": 1, **asdict(self)}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Nieobsługiwana wersja pliku spotkania.")
        items = [Item.from_dict(i) for i in data.get("items", [])]
        removed = [Item.from_dict(i) for i in data.get("removed", [])]
        ids = [i.id for i in items + removed]
        if len(set(ids)) != len(ids):
            raise ValueError("Powtórzone identyfikatory punktów.")
        recordings, transcripts = data.get("recordings", []), data.get("transcripts", [])
        if not all(isinstance(v, list) and all(isinstance(i, dict) for i in v)
                   for v in (recordings, transcripts)):
            raise ValueError("Nieprawidłowe załączniki spotkania.")
        screenshots = data.get("screenshots", [])
        if not isinstance(screenshots, list) or not all(isinstance(i, dict) for i in screenshots):
            raise ValueError("Nieprawidłowe zrzuty ekranu.")
        for recording in recordings:
            if not isinstance(recording.get("path", ""), str) or not isinstance(recording.get("markers", []), list):
                raise ValueError("Nieprawidłowe nagranie.")
            for marker in recording.get("markers", []):
                if not isinstance(marker, dict) or not isinstance(marker.get("item_id"), str):
                    raise ValueError("Nieprawidłowy znacznik.")
                seconds = marker.get("seconds", 0)
                if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
                    raise ValueError("Nieprawidłowy czas znacznika.")
        for transcript in transcripts:
            if not isinstance(transcript.get("text", ""), str):
                raise ValueError("Nieprawidłowa transkrypcja.")
        for screenshot in screenshots:
            if not isinstance(screenshot.get("path", ""), str):
                raise ValueError("Nieprawidłowy plik zrzutu.")
        return cls(items, removed, recordings, transcripts, screenshots)
