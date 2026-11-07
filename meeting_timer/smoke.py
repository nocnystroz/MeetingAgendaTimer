"""Explicit diagnostic mode; synthetic data only, no recording or network requests."""

import json
import os
import tempfile
from pathlib import Path

from PySide6.QtGui import QPdfWriter

from .exporting import markdown, pdf_document
from .parser import parse_agenda
from .theme import icon
from .windows import MainWindow


def run(app, full=False):
    with tempfile.TemporaryDirectory(prefix="licznik-smoke-") as temporary:
        os.environ["MEETING_TIMER_DATA_DIR"] = temporary
        window = MainWindow()
        window.tick_timer.stop()
        window.replace_items(parse_agenda("Łódź — 1 min\nDecyzje — 2 min"))
        window.notes.setPlainText("Test syntetyczny")
        window.engine.start()
        window.engine.seek(61)
        window.tick()
        assert window.counter.title.text() == "Decyzje"
        assert not icon("clock").isNull()
        window.counter.pin.setChecked(True)
        window.counter.pin.setChecked(False)
        window.toggle_audio()
        assert "Test syntetyczny" in markdown(window.meeting)
        pdf = Path(temporary) / "smoke.pdf"
        pdf_document(window.meeting).print_(QPdfWriter(str(pdf)))
        assert pdf.read_bytes().startswith(b"%PDF")
        assert window.save_session(clean=True)
        window.show_screenshots()
        window.screenshots_dialog.hide()
        if full:
            import numpy as np
            from PySide6.QtMultimedia import QWindowCapture
            assert np.zeros(1).size == 1
            assert QWindowCapture is not None
        window.save_timer.stop()
        window.tray.hide()
        window.quitting = True
        window.close()
        window.counter.close()
        app.processEvents()
        report = {"ok": True, "full": full, "gui": True, "pdf": True, "network_requests": 0}
        if output := os.environ.get("MEETING_TIMER_SMOKE_OUTPUT"):
            Path(output).write_text(json.dumps(report, indent=2), encoding="utf-8")
        elif sys_stdout_available():
            print(json.dumps(report))
        return 0


def sys_stdout_available():
    import sys
    return sys.stdout is not None
