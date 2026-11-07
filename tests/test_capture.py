import time

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from meeting_timer.model import Item, Meeting
from meeting_timer.windows import MainWindow


def test_screenshot_saved_assigned_and_limit(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setenv("MEETING_TIMER_DATA_DIR", str(tmp_path))
    window = MainWindow()
    window.tick_timer.stop()
    window.replace_items([Item("Bieżący punkt", 60)])
    window.show_screenshots()
    dialog = window.screenshots_dialog
    dialog.directory.setText(str(tmp_path))
    dialog.limit.setValue(1)
    dialog.running = True
    image = QImage(80, 60, QImage.Format.Format_RGB32)
    image.fill(QColor("#26b7a4"))
    dialog.save_image(image)
    deadline = time.monotonic() + 3
    while not window.meeting.screenshots and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert len(window.meeting.screenshots) == 1
    entry = window.meeting.screenshots[0]
    assert entry["item_id"] == window.meeting.items[0].id
    assert QImage(entry["path"]).size() == image.size()
    assert not dialog.running
    assert not list(tmp_path.glob("*.part"))
    restored = Meeting.from_dict(window.meeting.to_dict())
    assert restored.screenshots == window.meeting.screenshots
    app.processEvents()
    dialog.stop()
    window.save_timer.stop()
    window.tray.hide()
    window.quitting = True
    window.close()
    app.processEvents()


def test_empty_capture_stops_without_fallback(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setenv("MEETING_TIMER_DATA_DIR", str(tmp_path))
    window = MainWindow()
    window.tick_timer.stop()
    window.show_screenshots()
    dialog = window.screenshots_dialog
    dialog.running = True
    dialog.save_image(QImage())
    assert not dialog.running
    assert not window.meeting.screenshots
    assert "pusty obraz" in dialog.status.text()
    window.save_timer.stop()
    window.tray.hide()
    window.quitting = True
    window.close()
    app.processEvents()
