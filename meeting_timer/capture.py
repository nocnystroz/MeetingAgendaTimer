"""Periodic local still images. No video encoder; optional Qt window capture."""

import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from .audio_ui import Worker
from .windows import button, label


class ScreenshotDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle("Automatyczne zrzuty ekranu lub okna")
        self.resize(680, 300)
        self.running = False
        self.pending = False
        self.awaiting_frame = False
        self.count = 0
        self.worker = None
        self.capture = self.capture_session = self.sink = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.grab)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.setInterval(8000)
        self.timeout.timeout.connect(lambda: self.fail("System nie udostępnił obrazu okna. Sprawdź uprawnienia i dostępność wybranego okna."))
        layout = QVBoxLayout(self)
        tip = label("Zapis lokalny do PNG, bez wysyłania do API. System może wymagać uprawnienia do przechwytywania ekranu. Zrzuty mogą zawierać poufne informacje.", "muted")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        row = QHBoxLayout()
        self.source = QComboBox()
        self.refresh_screens()
        row.addWidget(self.source, 1)
        self.refresh = button("Wykryj okna", self.refresh_windows)
        row.addWidget(self.refresh)
        layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(label("Co (sekundy):"))
        self.interval = QSpinBox()
        self.interval.setRange(1, 86400)
        self.interval.setValue(30)
        self.interval.valueChanged.connect(self.change_interval)
        row.addWidget(self.interval)
        row.addWidget(label("Limit zrzutów:"))
        self.limit = QSpinBox()
        self.limit.setRange(1, 10000)
        self.limit.setValue(200)
        row.addWidget(self.limit)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.directory = QLineEdit(str(owner.directory / "screenshots"))
        row.addWidget(self.directory, 1)
        row.addWidget(button("Katalog…", self.choose_directory))
        layout.addLayout(row)
        row = QHBoxLayout()
        self.start_button = button("Rozpocznij zrzuty", self.start, primary=True)
        row.addWidget(self.start_button)
        self.stop_button = button("Zatrzymaj", self.stop)
        self.stop_button.setEnabled(False)
        row.addWidget(self.stop_button)
        row.addWidget(button("Otwórz katalog", self.open_directory))
        layout.addLayout(row)
        self.status = label("Gotowy. Interwał można zmieniać w trakcie. Zmiana źródła wymaga zatrzymania zrzutów.", "muted")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def refresh_screens(self):
        self.source.clear()
        for index, screen in enumerate(QGuiApplication.screens()):
            self.source.addItem(f"Ekran {index + 1}: {screen.name()}", ("screen", screen.name()))

    @property
    def busy(self):
        return self.pending or bool(self.worker and self.worker.isRunning())

    def refresh_windows(self):
        if self.running:
            return
        self.refresh_screens()
        try:
            from PySide6.QtMultimedia import QWindowCapture
            for window in QWindowCapture.capturableWindows():
                self.source.addItem("Okno: " + window.description(), ("window", window))
            self.status.setText("Wybierz ekran lub okno. Na Wayland przechwytywanie może wymagać osobnego portalu i nie być dostępne w tej wersji.")
        except ImportError:
            self.status.setText("Przechwytywanie wybranego okna wymaga paczki pełnej / dodatku [capture]. Zrzuty całego ekranu nie wymagają tego modułu.")

    def choose_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Katalog zrzutów", self.directory.text())
        if path:
            self.directory.setText(path)

    def open_directory(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        path = Path(self.directory.text()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def start(self):
        if self.running or self.busy or not self.source.currentData():
            return
        if QMessageBox.question(self, "Rozpocząć automatyczne zrzuty?",
                                f"Źródło: {self.source.currentText()}\nCo {self.interval.value()} s, do {self.limit.value()} plików PNG.\n\nZrzuty mogą zawierać prywatne dane. Będą zapisywane w wybranym katalogu; aplikacja nie wyśle ich do API.") != QMessageBox.StandardButton.Yes:
            return
        try:
            Path(self.directory.text()).expanduser().mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError:
            self.fail("Nie można utworzyć katalogu zrzutów.")
            return
        self.target = self.source.currentData()
        if self.target[0] == "window":
            try:
                from PySide6.QtMultimedia import QMediaCaptureSession, QVideoSink, QWindowCapture
                if not self.target[1].isValid():
                    self.fail("Wybrane okno nie jest już dostępne. Odśwież listę i wybierz je ponownie.")
                    return
                if self.capture:
                    self.capture.deleteLater()
                    self.capture_session.deleteLater()
                    self.sink.deleteLater()
                self.capture = QWindowCapture(self)
                self.capture_session = QMediaCaptureSession(self)
                self.sink = QVideoSink(self)
                self.capture_session.setWindowCapture(self.capture)
                self.capture_session.setVideoSink(self.sink)
                self.capture.setWindow(self.target[1])
                self.sink.videoFrameChanged.connect(self.frame)
                self.capture.errorOccurred.connect(lambda *args: self.fail("Przechwycenie tego okna nie powiodło się. Sprawdź uprawnienia systemu. Nie przełączono na cały ekran."))
            except (ImportError, RuntimeError):
                self.fail("Przechwytywanie okna jest niedostępne. Użyj paczki z opcją [capture].")
                return
        self.running = True
        self.count = 0
        self.source.setEnabled(False)
        self.directory.setEnabled(False)
        self.refresh.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.timer.start(self.interval.value() * 1000)
        self.owner.screenshot_status.setText("● Zrzuty aktywne")
        self.status.setText("Zrzuty aktywne. Zamknięcie tego okna nie zatrzymuje cyklu; użyj Zatrzymaj.")
        QTimer.singleShot(0, self.grab)

    def change_interval(self, value):
        if self.running:
            self.timer.start(value * 1000)

    def grab(self):
        if not self.running or self.pending:
            return
        if self.count >= self.limit.value():
            self.stop()
            self.status.setText("Osiągnięto limit zrzutów. Zapisane pliki pozostają na dysku.")
            return
        if self.target[0] == "window":
            self.pending = True
            self.awaiting_frame = True
            if not self.target[1].isValid():
                self.fail("Wybrane okno zamknięto. Zrzuty zatrzymano.")
                return
            self.timeout.start()
            self.capture.start()
        else:
            screen = next((s for s in QGuiApplication.screens() if s.name() == self.target[1]), None)
            if screen is None:
                self.fail("Wybrany ekran odłączono. Zrzuty zatrzymano.")
                return
            image = screen.grabWindow(0).toImage()
            self.save_image(image)

    def frame(self, frame):
        if not self.awaiting_frame or not self.running:
            return
        self.awaiting_frame = False
        self.timeout.stop()
        image = frame.toImage().copy()
        self.capture.stop()
        self.save_image(image)

    def save_image(self, image):
        if image.isNull():
            self.fail("Otrzymano pusty obraz. System nie udostępnia tego źródła lub brakuje uprawnienia do przechwytywania.")
            return
        self.pending = True
        path = Path(self.directory.text()).expanduser() / f"zrzut-{time.time_ns()}.png"
        snap = self.owner.engine.snapshot()
        item = self.owner.meeting.items[snap.index] if snap.index >= 0 else None
        metadata = {"path": str(path), "created_at": time.time(), "source": self.source.currentText(),
                    "item_id": item.id if item else None, "title": item.title if item else "",
                    "cursor": self.owner.engine.cursor, "width": image.width(), "height": image.height()}
        def operation():
            # Write a private temporary PNG, then atomically replace. Never leave a half PNG.
            import os
            temporary = path.with_suffix(".part")
            try:
                fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
                if not image.save(str(temporary), "PNG"):
                    raise ValueError("Nie udało się zapisać zrzutu. Sprawdź wolne miejsce.")
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
            return metadata
        self.worker = Worker(operation, self)
        self.worker.result.connect(self.saved)
        self.worker.error.connect(self.fail)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.release_worker)
        self.worker.start()

    def release_worker(self):
        self.worker = None

    def saved(self, metadata):
        self.pending = False
        self.count += 1
        self.owner.meeting.screenshots.append(metadata)
        self.owner.schedule_save()
        self.status.setText(f"Zapisano {self.count} / {self.limit.value()} · {Path(metadata['path']).name}")
        if self.running and self.count >= self.limit.value():
            self.stop()
            self.status.setText(f"Osiągnięto limit: {self.count} zrzutów. Zapis zatrzymany.")

    def stop(self):
        self.running = False
        self.awaiting_frame = False
        self.timer.stop()
        self.timeout.stop()
        if self.capture:
            self.capture.stop()
        if not self.worker or not self.worker.isRunning():
            self.pending = False
        self.source.setEnabled(True)
        self.directory.setEnabled(True)
        self.refresh.setEnabled(True)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.owner.screenshot_status.setText("")
        self.status.setText("Zrzuty zatrzymane. Pliki pozostają w wybranym katalogu.")

    def fail(self, text):
        self.stop()
        self.pending = bool(self.worker and self.worker.isRunning())
        self.status.setText(text)
        self.owner.screenshot_status.setText("Błąd zrzutów")
        self.owner.statusBar().showMessage(text)

    def closeEvent(self, event):
        if self.owner.quitting:
            event.accept()
        else:
            self.hide()
            event.ignore()
