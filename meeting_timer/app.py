import os
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from .storage import atomic_json, data_directory
from .theme import apply_theme, icon
from .windows import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Licznik spotkaniowy")
    app.setOrganizationName("Licznik spotkaniowy")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(icon("clock"))
    if "--smoke-test" in sys.argv or "--smoke-test-full" in sys.argv:
        from .smoke import run
        return run(app, full="--smoke-test-full" in sys.argv)
    directory = data_directory()
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError:
        QMessageBox.critical(None, "Brak dostępu do danych", "Nie można utworzyć katalogu danych. Ustaw MEETING_TIMER_DATA_DIR na katalog z prawem zapisu.")
        return 1
    lock = QLockFile(str(directory / "session.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, "Program już działa", "Sprawdź pasek zadań lub ikonę zegara w zasobniku. Druga kopia nie została uruchomiona.")
        return 0
    # The lock guarantees no other instance is using these private temporary chunks.
    cache = directory / ".transcription-cache"
    if cache.is_dir() and not cache.is_symlink():
        for temporary in cache.glob("job-*"):
            if temporary.is_dir() and not temporary.is_symlink():
                try:
                    shutil.rmtree(temporary)
                except OSError:
                    pass  # Do not block access to the meeting when temporary cleanup fails.
    apply_theme(app, system_palette=app.palette())
    window = MainWindow()
    window.show()
    QTimer.singleShot(0, window.restore)
    if marker := os.environ.get("MEETING_TIMER_READY_FILE"):
        QTimer.singleShot(0, lambda: atomic_json(Path(marker), {"ready": True}))
    result = app.exec()
    lock.unlock()
    return result
