import string

import pytest
from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QApplication, QDialog

from meeting_timer.documents import TermsDialog, ensure_accepted, terms_text, terms_version
from meeting_timer.i18n import catalog, set_language, tr
from meeting_timer.model import Item
from meeting_timer.parser import parse_agenda
from meeting_timer.storage import read_json
from meeting_timer.version import version
from meeting_timer.windows import MainWindow


@pytest.fixture
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    set_language("pl", app)
    monkeypatch.setenv("MEETING_TIMER_DATA_DIR", str(tmp_path))
    window = MainWindow()
    window.tick_timer.stop()
    yield window
    if window.audio_panel:
        for worker in list(window.audio_panel.workers):
            worker.wait(5000)
        app.processEvents()
    window.save_timer.stop()
    window.tray.hide()
    window.quitting = True
    window.close()
    window.counter.close()
    app.processEvents()
    set_language("pl", app)


@pytest.mark.parametrize("code,start,theme,notes", [
    ("en", "Start", "System theme", "Notes"),
    ("de", "Starten", "Systemdesign", "Notizen"),
    ("fr", "Démarrer", "Thème système", "Notes"),
])
def test_live_language_preserves_agenda_notes_and_time(window, code, start, theme, notes):
    window.replace_items([Item("Notatki", 120, notes="Poufne dane nie są tłumaczone")])
    window.engine.start()
    window.engine.seek(12)
    window.engine.toggle_pause()
    before = window.meeting.to_dict()
    window.language_combo.setCurrentIndex(["pl", "en", "de", "fr"].index(code))
    assert window.theme.itemText(0) == theme
    assert window.tabs.tabText(0) == notes
    assert window.engine.snapshot().remaining == pytest.approx(108, abs=0.1)
    assert window.counter.title.text() == "Notatki"
    assert window.meeting.to_dict() == before
    assert tr("Rozpocznij") == start


def test_catalog_has_all_languages_and_same_placeholders():
    formatter = string.Formatter()
    def fields(text):
        return {name for _, name, _, _ in formatter.parse(text) if name is not None}
    for source, targets in catalog().items():
        assert set(targets) == {"en", "de", "fr"}
        for value in targets.values():
            assert value and fields(value) == fields(source), source


@pytest.mark.parametrize("text", ["Ergebnisse — 15 Minuten", "Bilan — 15 minutes", "Overview — 15 minutes"])
def test_localized_agenda_units(text):
    assert parse_agenda(text)[0].seconds == 900


def test_specific_start_time_waits_without_changing_duration(window):
    window.replace_items([Item("Start później", 60)])
    window.mode.setCurrentIndex(2)
    window.scheduled_start.setDateTime(QDateTime.currentDateTime().addSecs(120))
    window.play_pause()
    snap = window.engine.snapshot()
    assert snap.state == "waiting"
    assert 115 < snap.remaining <= 120
    assert window.meeting.items[0].seconds == 60


def test_empty_transcript_list_explains_and_provider_is_visible(window):
    window.toggle_audio()
    panel = window.audio_panel
    assert panel.transcript_choice.count() == 1
    assert "Brak zapisanych" in panel.transcript_choice.currentText()
    assert "OpenAI" in panel.provider.currentText()
    assert panel.transcript_entry is None


def test_detected_sources_are_available_in_dropdowns(window):
    window.toggle_audio()
    panel = window.audio_panel
    panel.sources_found([{"id": "mic", "name": "Mikrofon testowy", "loopback": False},
                         {"id": "speaker", "name": "Monitor testowy", "loopback": True}])
    assert panel.mic.count() == 2
    assert panel.system.count() == 3
    panel.mic.setCurrentIndex(1)
    panel.system.setCurrentIndex(1)
    assert panel.source_selection()[0] == ["mic", "speaker"]


def test_terms_require_checkbox_and_are_remembered(tmp_path, monkeypatch, window):
    dialog = TermsDialog()
    assert not dialog.agree.isEnabled()
    dialog.consent.setChecked(True)
    assert dialog.agree.isEnabled()
    dialog.close()
    def accept(self):
        self.consent.setChecked(True)
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(TermsDialog, "exec", accept)
    assert ensure_accepted(tmp_path)
    stored = read_json(tmp_path / "consent.json")
    assert stored["terms_version"] == terms_version() and stored["accepted"] is True
    monkeypatch.setattr(TermsDialog, "exec", lambda self: pytest.fail("Asked again without terms change"))
    assert ensure_accepted(tmp_path)
    assert "Zgody uczestników" in terms_text("pl")
    assert "Participants' consent" in terms_text("en")


def test_terms_decline_creates_no_acceptance(tmp_path, monkeypatch, window):
    monkeypatch.setattr(TermsDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    assert not ensure_accepted(tmp_path)
    assert not (tmp_path / "consent.json").exists()


def test_version_is_commit_number():
    assert version().rstrip("*").isdigit()
