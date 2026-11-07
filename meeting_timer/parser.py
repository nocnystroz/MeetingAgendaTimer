"""Strict, local agenda parsing with actionable line numbers."""

import re
from dataclasses import dataclass

from .model import Item

CLOCK = r"(?:[01]?\d|2[0-3]):[0-5]\d"
RANGE = re.compile(rf"^({CLOCK})\s*[-–—]\s*({CLOCK})\s*[:|–—-]?\s*(.+)$")
DURATION = re.compile(r"(?<![\w.])(?P<n>\d+(?:[.,]\d+)?)\s*(?P<u>godz\.?|h|min\.?|m|sek\.?|s)(?!\w)", re.I)


@dataclass
class ParseError(ValueError):
    errors: list[str]

    def __str__(self):
        return "\n".join(self.errors)


def _clock(value):
    hour, minute = map(int, value.split(":"))
    return hour * 3600 + minute * 60


def parse_agenda(text: str) -> list[Item]:
    items, errors = [], []
    mode = None
    day, previous_end, previous_start = 0, None, None
    for number, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r"^\s*(?:(?:\d+[.)]|[-*•])\s+)?", "", raw).strip()
        if not line:
            continue
        match = RANGE.fullmatch(line)
        if match:
            start, end = _clock(match[1]), _clock(match[2])
            if previous_start is not None and start < previous_start:
                # Only a late-evening to early-morning transition implies midnight.
                if (previous_end is not None and previous_end >= day + 86400) or (previous_start >= 18 * 3600 and start <= 6 * 3600):
                    day += 86400
                else:
                    errors.append(f"Wiersz {number}: godziny nie są chronologiczne.")
            absolute = start + day
            if start == end:
                errors.append(f"Wiersz {number}: początek i koniec są takie same.")
            duration = (end - start) % 86400
            if previous_end is not None and absolute < previous_end:
                errors.append(f"Wiersz {number}: punkt nakłada się na poprzedni.")
            items.append(Item(match[3].strip(), max(1, duration), absolute))
            previous_start, previous_end = start, absolute + duration
            current_mode = "clock"
        else:
            matches = list(DURATION.finditer(line))
            seconds = 0
            for m in matches:
                unit = m["u"].lower().rstrip(".")
                factor = 3600 if unit in ("h", "godz") else 60 if unit in ("m", "min") else 1
                seconds += float(m["n"].replace(",", ".")) * factor
            title = DURATION.sub("", line).strip(" \t-–—:|()[]")
            if not matches or not title or not 1 <= seconds <= 604800 or seconds != int(seconds):
                errors.append(f"Wiersz {number}: użyj „Tytuł — 15 min” lub „10:00–10:15 Tytuł”.")
                continue
            # A clock-like prefix must not silently turn into a duration-based item.
            if re.match(r"^\d{1,2}:\d", title):
                errors.append(f"Wiersz {number}: podaj poprawny przedział godzinowy.")
                continue
            items.append(Item(title, int(seconds)))
            current_mode = "duration"
        if mode is not None and current_mode != mode:
            errors.append(f"Wiersz {number}: nie mieszaj przedziałów godzinowych i czasów trwania.")
        mode = current_mode
    if errors:
        raise ParseError(errors)
    if not items:
        raise ParseError(["Wklej co najmniej jeden punkt agendy z czasem."])
    return items
