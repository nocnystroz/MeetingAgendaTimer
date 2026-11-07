import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QPdfWriter
from PySide6.QtWidgets import QApplication, QMessageBox

from meeting_timer.engine import TimerEngine
from meeting_timer.exporting import markdown, pdf_document
from meeting_timer.model import Item
from meeting_timer.parser import parse_agenda
from meeting_timer.storage import read_json
from meeting_timer.windows import MainWindow


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, monkeypatch, tmp_path):
    monkeypatch.setenv("MEETING_TIMER_DATA_DIR", str(tmp_path))
    widget = MainWindow()
    widget.tick_timer.stop()
    monkeypatch.setattr(widget, "message", lambda *args: None)
    yield widget
    widget.tick_timer.stop()
    widget.save_timer.stop()
    widget.tray.hide()
    widget.counter.hide()
    widget.hide()
    widget.deleteLater()
    app.processEvents()


def test_notes_selection_does_not_switch_timer(window):
    window.replace_items(parse_agenda("A — 1 min\nB — 2 min"))
    window.engine.start()
    original_id = window.engine.current_id
    window.notes.setPlainText("Notatki punktu A")
    window.agenda_list.setCurrentRow(1)
    window.notes.setPlainText("Notatki punktu B")
    window.tick()
    assert window.engine.current_id == original_id
    assert window.counter.title.text() == "A"
    assert window.meeting.items[0].notes == "Notatki punktu A"
    assert window.meeting.items[1].notes == "Notatki punktu B"
    assert "Notatki" not in window.counter.title.text()


def test_reorder_and_title_preserve_notes(window):
    window.replace_items(parse_agenda("A 1 min\nB 2 min\nC 3 min"))
    window.engine.start()
    window.agenda_list.setCurrentRow(1)
    window.notes.setPlainText("B notes")
    point_id = window.selected_id
    window.edit_title("Nowy tytuł")
    window.move_item(1)
    assert window.meeting.items[2].id == point_id
    assert window.meeting.items[2].notes == "B notes"
    assert window.engine.snapshot().index == 0


def test_tasks_export_and_pdf(window, tmp_path):
    window.replace_items([Item("Łódź <tag>", 60, notes="<img src='https://invalid.test/a'>")])
    window.add_task()
    window.tasks.item(0, 1).setText("Wyślij ofertę")
    window.tasks.item(0, 2).setText("Ola")
    window.tasks.item(0, 0).setCheckState(Qt.CheckState.Checked)
    result = markdown(window.meeting)
    assert "[x] Wyślij ofertę — Ola" in result
    assert "<img" not in markdown(window.meeting, notes=False)
    document = pdf_document(window.meeting)
    assert "<img" in document.toPlainText()  # Literal text; never interpreted as external content.
    path = tmp_path / "test.pdf"
    document.print_(QPdfWriter(str(path)))
    assert path.read_bytes().startswith(b"%PDF")


def test_crash_restore_paused_without_recording(window, monkeypatch):
    window.replace_items(parse_agenda("A 1 min\nB 2 min"))
    window.engine.start()
    window.engine.seek(75)
    window.engine.snapshot()
    window.notes.setPlainText("Przywróć mnie")
    window.save_session()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    restored = MainWindow()
    restored.tick_timer.stop()
    try:
        restored.restore()
        assert restored.engine.started and restored.engine.paused
        assert restored.engine.snapshot().index == 1
        assert restored.meeting.items[0].notes == "Przywróć mnie"
        assert restored.recorder is None
        assert restored.audio_panel is None
    finally:
        restored.save_timer.stop()
        restored.tray.hide()
        restored.deleteLater()


def test_session_and_template_have_no_key(window):
    window.toggle_audio()
    window.audio_panel.api_key.setText("very-secret-test-key")
    window.save_session(clean=True)
    assert "very-secret-test-key" not in window.session_path.read_text()
    assert read_json(window.session_path)["clean"]


def test_no_tray_minimizes_instead_of_disappearing(window, monkeypatch):
    from PySide6.QtWidgets import QSystemTrayIcon
    monkeypatch.setattr(QSystemTrayIcon, "isSystemTrayAvailable", lambda: False)
    window.show()
    window.hide_to_tray(window)
    assert window.isMinimized()


def test_pin_and_compact_do_not_reset_clock(window):
    window.replace_items([Item("A", 120)])
    window.engine.start()
    window.engine.seek(12)
    window.counter.pin.setChecked(True)
    window.counter.compact.setChecked(True)
    window.theme.setCurrentIndex(2)
    assert 107 < window.engine.snapshot().remaining <= 108
    assert window.counter.windowFlags() & Qt.WindowType.WindowStaysOnTopHint


def test_replace_retains_notes_and_reenables_mode(window):
    window.replace_items([Item("A", 60, notes="Zachowaj")])
    old_id = window.meeting.items[0].id
    window.engine.start()
    window.mode.setEnabled(False)
    window.replace_items([Item("B", 120)])
    assert window.meeting.removed[0].id == old_id
    assert window.meeting.removed[0].notes == "Zachowaj"
    assert not window.engine.started
    assert window.mode.isEnabled()


def test_engine_independent_of_note_editing(window):
    clock = [0]
    window.replace_items(parse_agenda("A 1 min\nB 1 min"))
    window.engine = TimerEngine(window.meeting.items, lambda: clock[0])
    window.engine.start()
    for n in range(100):
        window.notes.setPlainText("x" * n)
    clock[0] = 61
    window.tick()
    assert window.counter.title.text() == "B"
