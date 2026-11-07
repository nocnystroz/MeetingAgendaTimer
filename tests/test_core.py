
import pytest

from meeting_timer.engine import TimerEngine, format_time
from meeting_timer.model import Item, Meeting, Task
from meeting_timer.parser import ParseError, parse_agenda
from meeting_timer.storage import load_meeting, save_meeting, template_data


class Clock:
    value = 0

    def __call__(self):
        return self.value


def engine(text="A — 1 min\nB — 2 min"):
    clock = Clock()
    return TimerEngine(parse_agenda(text), clock, lambda: 1000 + clock.value), clock


def test_formats():
    result = parse_agenda("1. Wyniki — 15 min\n• Plan (1 h 5 min)\n- Koniec 30 sek")
    assert [(i.title, i.seconds) for i in result] == [("Wyniki", 900), ("Plan", 3900), ("Koniec", 30)]
    assert parse_agenda("Powitanie — 1,5 min")[0].seconds == 90


@pytest.mark.parametrize("text", ["", "Agenda", "A 0 min", "10:00–10:15 A\nB 2 min",
                                    "10:00–11:00 A\n10:30–11:10 B", "24:00–25:00 A",
                                    "10:00–10:00 A", "10:00–11:00 A\n09:00–09:30 B"])
def test_errors(text):
    with pytest.raises(ParseError):
        parse_agenda(text)


def test_errors_include_line_numbers():
    with pytest.raises(ParseError, match="Wiersz 3"):
        parse_agenda("A 1 min\n\nB")


def test_midnight_and_gap():
    items = parse_agenda("23:50–00:10 A\n00:15–00:30 B")
    assert items[1].scheduled == 86400 + 15 * 60
    timer = TimerEngine(items)
    assert timer.slots() == [(0, 1200), (1500, 2400)]


def test_late_refresh_pause_finish():
    timer, clock = engine()
    timer.start()
    clock.value = 72
    assert timer.snapshot().index == 1
    assert timer.snapshot().remaining == 108
    timer.toggle_pause()
    clock.value = 100
    assert timer.snapshot().remaining == 108
    timer.toggle_pause()
    clock.value = 208
    assert timer.snapshot().state == "finished"


def test_overtime_and_extension():
    timer, clock = engine()
    timer.auto = False
    timer.start()
    clock.value = 75
    assert timer.snapshot().remaining == -15
    timer.add_time(60)
    assert timer.snapshot().remaining == 45
    assert timer.baseline_end == 1180
    timer.jump(1)
    assert timer.snapshot().remaining == 120


def test_schedule_wait_gap_late_start():
    timer, clock = engine("10:00–10:01 A\n10:02–10:03 B")
    timer.start(scheduled_epoch=1030)
    assert timer.snapshot().state == "waiting"
    clock.value = 100
    assert timer.snapshot().state == "waiting"
    assert timer.snapshot().remaining == 50
    clock.value = 155
    assert timer.snapshot().index == 1
    assert timer.snapshot().remaining == 55
    timer.toggle_pause()
    clock.value += 100
    timer.toggle_pause()
    assert timer.snapshot().remaining == 55


def test_mutation_preserves_current_elapsed():
    timer, clock = engine()
    timer.start()
    clock.value = 75
    current = timer.items[1]
    timer.mutate(lambda: timer.items.insert(0, Item("Nowy", 300)))
    assert timer.snapshot().remaining == 105
    assert timer.current_id == current.id


def test_save_restore_templates(tmp_path):
    meeting = Meeting([Item("Łódź", 60, notes="Poufne", tasks=[Task("Zrobić", "Ola", "jutro", True)])])
    save_meeting(tmp_path / "session.json", meeting)
    loaded = load_meeting(tmp_path / "session.json")
    assert loaded.to_dict() == meeting.to_dict()
    template = Meeting.from_dict(template_data(meeting))
    assert template.items[0].notes == ""
    assert not template.items[0].tasks
    assert template.items[0].id != meeting.items[0].id


def test_duplicate_ids_rejected():
    item = Item("A", 60).to_dict()
    with pytest.raises(ValueError, match="identyfikatory"):
        Meeting.from_dict({"version": 1, "items": [item, item]})


def test_format_time():
    assert format_time(-150) == "+02:30"
    assert format_time(3601) == "1:00:01"
    assert format_time(0.1) == "00:01"


@pytest.mark.parametrize("value", ["NaN", "Infinity", "1e999"])
def test_nonfinite_storage_rejected(tmp_path, value):
    from meeting_timer.storage import read_json
    path = tmp_path / "broken.json"
    path.write_text('{"cursor": ' + value + '}')
    with pytest.raises(ValueError):
        read_json(path)


def test_long_overnight_range():
    items = parse_agenda("23:00–10:00 Noc\n10:15–11:00 Rano")
    assert items[1].scheduled == 86400 + 10 * 3600 + 15 * 60


def test_manual_next_after_last_finishes_and_previous_reopens():
    timer, clock = engine("Ostatni — 1 min")
    timer.auto = False
    timer.start()
    clock.value = 75
    assert timer.snapshot().state == "overtime"
    timer.jump(1)
    assert timer.snapshot().state == "finished"
    timer.jump(0)
    assert timer.snapshot().state == "running"


@pytest.mark.parametrize("text,expected", [
    ("15 minut — Wyniki", [("Wyniki", 900)]),
    ("1. Wyniki — 1 godz. 15 min", [("Wyniki", 4500)]),
    ("Wyniki 1h30min", [("Wyniki", 5400)]),
    ("Wyniki (00:15:00)", [("Wyniki", 900)]),
    ("Wyniki [15:00]", [("Wyniki", 900)]),
    ("Wyniki;15 min", [("Wyniki", 900)]),
    ('"Wyniki, ryzyka";15 min', [("Wyniki, ryzyka", 900)]),
    ("Temat\tCzas (min)\nWyniki\t15", [("Wyniki", 900)]),
    ("Nr\tTemat\tCzas (min)\n1\tWyniki\t15", [("Wyniki", 900)]),
    ("| Temat | Czas |\n|---|---|\n| Wyniki | 15 min |", [("Wyniki", 900)]),
    ("10:00\t10:15\tWyniki", [("Wyniki", 900)]),
    ("10:00 Wyniki\n10:15 Decyzje (10 min)", [("Wyniki", 900), ("Decyzje", 600)]),
    ("10:00 Wyniki\n10:15 Decyzje\n10:25 Koniec", [("Wyniki", 900), ("Decyzje", 600)]),
    ("10.00–10.15 Wyniki", [("Wyniki", 900)]),
    ("Agenda:\n1.Wyniki 15 min", [("Wyniki", 900)]),
])
def test_pasted_agenda_formats(text, expected):
    assert [(i.title, i.seconds) for i in parse_agenda(text)] == expected


def test_start_times_need_explicit_end():
    with pytest.raises(ParseError, match="ostatni punkt"):
        parse_agenda("10:00 Wyniki\n10:15 Decyzje")
