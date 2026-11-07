"""Local agenda parser: plain text, spreadsheet columns, CSV and Markdown tables."""

import csv
import re
from dataclasses import dataclass

from .model import Item

CLOCK = r"(?:[01]?\d|2[0-3]):[0-5]\d"
RANGE = re.compile(rf"^({CLOCK})\s*[-–—]\s*({CLOCK})\s*[:|–—-]?\s*(.+)$")
START = re.compile(rf"^({CLOCK})\s+(?:[-–—:|]\s*)?(.+)$")
DURATION = re.compile(
    r"(?<![\w.])(?P<n>\d+(?:[.,]\d+)?)\s*"
    r"(?P<u>godzin(?:a|y)?|godz\.?|hours?|heures?|hrs?|stunden?|std\.?|h|minut(?:a|y|en)?|minutes?|mins?\.?|m|"
    r"sekund(?:a|y|en)?|sek\.?|seconds?|secondes?|secs?\.?|s)(?!\w)", re.I
)
BRACKET_TIME = re.compile(r"[\[(](\d{1,3}):([0-5]\d)(?::([0-5]\d))?[\])]")
HEADER_TITLE = {"temat", "tytuł", "tytul", "punkt", "agenda", "topic", "title", "thema", "titel", "sujet", "point"}
HEADER_TIME = ("czas", "duration", "start", "koniec", "godzina", "time", "end", "dauer", "zeit", "durée", "début", "fin")


@dataclass
class ParseError(ValueError):
    errors: list[str]

    def __str__(self):
        return "\n".join(self.errors)


@dataclass
class Row:
    title: str
    seconds: int | None
    start: int | None
    number: int
    end: int | None = None


def _clock(value):
    hour, minute = map(int, value.split(":"))
    return hour * 3600 + minute * 60


def _duration(line):
    line = re.sub(r"(?<=\d)(h|m|min|s)(?=\d)", r"\1 ", line, flags=re.I)
    matches = list(DURATION.finditer(line))
    seconds = 0
    for match in matches:
        unit = match["u"].lower().rstrip(".")
        factor = 3600 if unit.startswith(("h", "godz", "st")) else 60 if unit.startswith("m") else 1
        seconds += float(match["n"].replace(",", ".")) * factor
    title = DURATION.sub("", line)
    if not matches and (match := BRACKET_TIME.search(line)):
        a, b, c = match.groups()
        seconds = int(a) * 60 + int(b) if c is None else int(a) * 3600 + int(b) * 60 + int(c)
        title = line[:match.start()] + line[match.end():]
        matches = [match]
    title = title.strip(" \t-–—:|;,()[]")
    if not matches:
        return None, title
    if not 1 <= seconds <= 604800 or seconds != int(seconds):
        raise ValueError("czas musi być dodatni, w pełnych sekundach, do 7 dni.")
    return int(seconds), title


def _columns(line):
    separator = next((s for s in ("\t", "|", ";") if s in line), None)
    if separator is None and "," in line:
        # Decimal commas stay untouched; CSV needs a comma outside a number.
        if re.search(r"(?<!\d),|,(?!\d)", line):
            separator = ","
    if separator is None:
        return [line]
    try:
        return [cell.strip() for cell in next(csv.reader([line], delimiter=separator)) if cell.strip()]
    except csv.Error as exc:
        raise ValueError("nieprawidłowy wiersz tabeli/CSV.") from exc


def parse_agenda(text: str) -> list[Item]:
    if len(text) > 1_000_000:
        raise ParseError(["Agenda przekracza limit 1 MB."])
    rows, errors = [], []
    header_unit = None
    header_index = None
    header_duration = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r"^\s*(?:(?:\d+[.)](?!\d)\s*)|(?:[-–—*•]\s+))?(?:\[[ xX]\]\s*)?", "", raw).strip()
        if not line:
            continue
        # Explicit structural headings, not arbitrary unrecognized lines.
        if re.fullmatch(r"#{0,3}\s*(?:agenda|plan spotkania)\s*:?", line, re.I):
            continue
        if re.fullmatch(r"\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?", line):
            continue
        try:
            cells = _columns(line)
            lowered = [cell.lower() for cell in cells]
            if any(cell in HEADER_TITLE for cell in lowered) and any(
                any(word in cell for word in HEADER_TIME) for cell in lowered
            ):
                header_unit = "min" if any("min" in c for c in lowered) else "s" if any("sek" in c for c in lowered) else None
                header_index = next((i for i, c in enumerate(lowered) if c in ("lp", "lp.", "nr", "#")), None)
                header_duration = next((i for i, c in enumerate(lowered) if c.startswith(("czas", "duration", "dauer", "durée")) and "start" not in c and "koniec" not in c), None)
                continue
            if header_index is not None:
                if header_duration is not None and header_duration > header_index:
                    duration_column = header_duration - 1
                else:
                    duration_column = header_duration
                cells = [cell for i, cell in enumerate(cells) if i != header_index]
            else:
                duration_column = header_duration
            clock_cells = [cell for cell in cells if re.fullmatch(CLOCK, cell)]
            if len(cells) > 1 and len(clock_cells) == 2:
                title = " ".join(cell for cell in cells if cell not in clock_cells)
                line = f"{clock_cells[0]}–{clock_cells[1]} {title}"
            elif len(cells) > 1:
                normalized = []
                for index, cell in enumerate(cells):
                    if header_unit and index == duration_column and re.fullmatch(r"\d+(?:[.,]\d+)?", cell):
                        cell += " " + header_unit
                    if re.fullmatch(r"\d{1,3}:[0-5]\d:[0-5]\d", cell):
                        cell = f"[{cell}]"
                    normalized.append(cell)
                if len(clock_cells) == 1:
                    start = clock_cells[0]
                    normalized = [cell for cell in normalized if cell != start]
                    line = start + " " + " ".join(normalized)
                else:
                    line = " ".join(normalized)
            # Common dotted clock notation, only for explicit ranges.
            line = re.sub(r"^([0-2]?\d)\.([0-5]\d)(\s*[-–—]\s*)([0-2]?\d)\.([0-5]\d)",
                          r"\1:\2\3\4:\5", line)
            if match := RANGE.fullmatch(line):
                start, end = _clock(match[1]), _clock(match[2])
                if start == end:
                    raise ValueError("początek i koniec są takie same.")
                rows.append(Row(match[3].strip(" |;-–—"), (end - start) % 86400, start, number, end))
            elif match := START.fullmatch(line):
                seconds, title = _duration(match[2])
                if not title:
                    raise ValueError("podaj tytuł punktu.")
                rows.append(Row(title, seconds, _clock(match[1]), number))
            else:
                seconds, title = _duration(line)
                if seconds is None or not title:
                    raise ValueError("użyj „Tytuł — 15 min”, „10:00–10:15 Tytuł” lub tabeli z czasem.")
                if re.search(r"\b\d{1,2}:\d", title):
                    raise ValueError("podaj poprawny przedział godzinowy lub czas w nawiasie [MM:SS].")
                rows.append(Row(title, seconds, None, number))
        except ValueError as exc:
            errors.append(f"Wiersz {number}: {exc}")
    if len(rows) > 5000:
        errors.append("Agenda przekracza limit 5000 punktów.")
    modes = {row.start is not None for row in rows}
    if len(modes) > 1:
        errors.append("Nie mieszaj przedziałów/godzin rozpoczęcia i samych czasów trwania.")
    if errors:
        raise ParseError(errors)
    if not rows:
        raise ParseError(["Wklej co najmniej jeden punkt agendy z czasem."])
    if True in modes:
        day = 0
        previous = None
        for row in rows:
            original_start = row.start
            if previous and original_start < previous.start % 86400:
                previous_crosses = previous.seconds is not None and previous.start + previous.seconds >= day + 86400
                if previous_crosses or (previous.start % 86400 >= 18 * 3600 and original_start <= 6 * 3600):
                    day += 86400
                else:
                    errors.append(f"Wiersz {row.number}: godziny nie są chronologiczne.")
            row.start += day
            if previous:
                if previous.seconds is None:
                    previous.seconds = row.start - previous.start
                if previous.seconds <= 0 or previous.start + previous.seconds > row.start:
                    errors.append(f"Wiersz {row.number}: punkt nakłada się na poprzedni lub ma ten sam początek.")
            previous = row
        last = rows[-1]
        if last.seconds is None:
            # Explicit end marker closes a list of starts, without inventing a final duration.
            if last.title.casefold().strip(".") in ("koniec", "koniec spotkania", "end", "ende", "fin") and len(rows) > 1:
                rows.pop()
            else:
                errors.append(f"Wiersz {last.number}: ostatni punkt wymaga czasu, np. „{last.title} (15 min)”, albo kolejnego wiersza „HH:MM Koniec”.")
    if errors:
        raise ParseError(errors)
    return [Item(row.title, row.seconds, row.start) for row in rows]
