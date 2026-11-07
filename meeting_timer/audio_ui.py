"""Lazily constructed audio/API controls. All blocking work stays off the GUI thread."""

import tempfile
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .engine import format_time
from .storage import atomic_json
from .transcription import MODEL, Cancelled, Transcriber, inspect_audio, wav_chunks
from .widgets import ComboBox
from .windows import button, label


class Worker(QThread):
    result = Signal(object)
    error = Signal(str)

    def __init__(self, operation, parent):
        super().__init__(parent)
        self.operation = operation

    def run(self):
        try:
            self.result.emit(self.operation())
        except Cancelled:
            self.error.emit("Anulowano. Przesłanych danych i ewentualnych kosztów nie można cofnąć.")
        except ValueError as exc:
            self.error.emit(str(exc))
        except Exception:
            self.error.emit("Nie udało się wykonać zadania. Sprawdź dostępność funkcji, uprawnienia i zależności opcjonalne.")
        finally:
            self.operation = None


class AudioPanel(QTabWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.workers = []
        self.recorder = None
        self.record_entry = None
        self.last_recording = None
        self.transcriber = None
        self.transcribing = False
        self.transcript_entry = None
        self.pending_restart = False
        self.make_recording_tab()
        self.make_transcript_tab()
        self.setMaximumHeight(340)

    @property
    def busy(self):
        return bool(self.workers or (self.recorder and self.recorder.active) or self.transcribing)

    def run_worker(self, operation, on_result, on_error=None):
        worker = Worker(operation, self)
        self.workers.append(worker)
        worker.result.connect(on_result, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(on_error or self.show_error, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(lambda: self.workers.remove(worker), Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def show_error(self, text):
        self.owner.message("Zadanie niedokończone", text)

    def make_recording_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        row = QHBoxLayout()
        self.mic, self.system = ComboBox(), ComboBox()
        self.mic.addItem("Mikrofon: nie wybrano", None)
        self.system.addItem("Dźwięk spotkania: nie wybrano", None)
        self.mic.setMinimumWidth(180)
        self.system.setMinimumWidth(180)
        row.addWidget(self.mic, 1)
        row.addWidget(self.system, 1)
        self.detect = button("Wykryj źródła", self.detect_sources)
        row.addWidget(self.detect)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.mix = ComboBox()
        self.mix.addItems(["Miks mono", "Rozdzielone kanały"])
        row.addWidget(self.mix)
        self.gains = []
        for text in ("Mikrofon ×", "Spotkanie ×"):
            row.addWidget(label(text))
            gain = QDoubleSpinBox()
            gain.setRange(0, 4)
            gain.setSingleStep(0.1)
            gain.setValue(1)
            self.gains.append(gain)
            row.addWidget(gain)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setFormat("Poziom %p%")
        row.addWidget(self.level)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.audio_dir = QLineEdit(str(owner_path(self.owner) / "recordings"))
        row.addWidget(self.audio_dir, 1)
        row.addWidget(button("Katalog…", self.choose_audio_directory))
        layout.addLayout(row)
        row = QHBoxLayout()
        self.test = button("Test źródeł (3 s)", self.test_sources)
        self.start = button("Nagraj", self.start_recording, "microphone", True)
        self.pause = button("Pauza nagrania", self.pause_recording)
        self.stop = button("Zatrzymaj i zapisz", self.stop_recording)
        self.segment = button("Nowy segment / źródła", self.switch_segment)
        for w in (self.test, self.start, self.pause, self.stop, self.segment):
            row.addWidget(w)
        layout.addLayout(row)
        self.audio_status = label("Audio działa lokalnie. Na macOS dźwięk systemowy wymaga udostępnionego źródła loopback/urządzenia wirtualnego. Pauza licznika nie zatrzymuje nagrania.", "muted")
        self.audio_status.setWordWrap(True)
        layout.addWidget(self.audio_status)
        self.addTab(widget, "Nagrywanie lokalne")

    def make_transcript_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.transcript_choice = ComboBox()
        self.transcript_choice.currentIndexChanged.connect(self.select_transcript)
        layout.addWidget(self.transcript_choice)
        row = QHBoxLayout()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Klucz OpenAI API — tylko bieżąca sesja")
        row.addWidget(self.api_key, 1)
        row.addWidget(button("Wczytaj z magazynu", self.load_key))
        row.addWidget(button("Zapamiętaj klucz", self.save_key))
        row.addWidget(button("Usuń klucz", self.delete_key))
        layout.addLayout(row)
        row = QHBoxLayout()
        self.audio_file = QLineEdit()
        self.audio_file.setPlaceholderText("Wybierz zakończone nagranie")
        row.addWidget(self.audio_file, 1)
        row.addWidget(button("Wybierz plik…", self.choose_audio_file))
        self.send = button("Transkrybuj…", self.transcribe, primary=True)
        row.addWidget(self.send)
        self.cancel = button("Anuluj", self.cancel_transcription)
        row.addWidget(self.cancel)
        layout.addLayout(row)
        self.transcript_text = QPlainTextEdit()
        self.transcript_text.setPlaceholderText("Wynik transkrypcji. Możesz go poprawić i wyeksportować z podsumowaniem.")
        self.transcript_text.textChanged.connect(self.edit_transcript)
        layout.addWidget(self.transcript_text, 1)
        layout.addWidget(button("Przypisz transkrypcję do wybranego punktu", self.assign_transcript))
        info_row = QHBoxLayout()
        self.api_status = label(f"OpenAI · {MODEL} · bez automatycznej wysyłki i ponawiania", "muted")
        info_row.addWidget(self.api_status, 1)
        info_row.addWidget(button("Eksport TXT", self.export_transcript))
        layout.addLayout(info_row)
        self.addTab(widget, "Opcjonalna transkrypcja API")
        self.reload_transcripts()

    def reload_transcripts(self):
        from PySide6.QtCore import QSignalBlocker
        with QSignalBlocker(self.transcript_choice):
            self.transcript_choice.clear()
            for index, value in enumerate(self.owner.meeting.transcripts):
                self.transcript_choice.addItem(f"{index + 1}. {Path(str(value.get('source', 'Nagranie'))).name}")
        self.select_transcript(self.transcript_choice.currentIndex())

    def select_transcript(self, index):
        if self.transcribing:
            return
        self.transcript_entry = self.owner.meeting.transcripts[index] if 0 <= index < len(self.owner.meeting.transcripts) else None
        self.transcript_text.setPlainText(self.transcript_entry.get("text", "") if self.transcript_entry else "")

    def detect_sources(self):
        self.detect.setEnabled(False)
        def operation():
            from .audio import devices
            return devices()
        self.run_worker(operation, self.sources_found, self.sources_error)

    def sources_error(self, text):
        self.detect.setEnabled(True)
        self.show_error(text + "\nWersja źródłowa: zainstaluj opcję [audio] do .venv. Na Linux potrzebna jest biblioteka libpulse i działający serwer PulseAudio/PipeWire.")

    def sources_found(self, values):
        self.detect.setEnabled(True)
        self.mic.clear()
        self.system.clear()
        self.mic.addItem("Mikrofon: nie wybrano", None)
        self.system.addItem("Spotkanie: nie wybrano", None)
        for value in values:
            combo = self.system if value["loopback"] else self.mic
            combo.addItem(value["name"], value["id"])
        # Physical/virtual inputs can also be used explicitly as the meeting source.
        for value in values:
            if not value["loopback"]:
                self.system.addItem("Wejście: " + value["name"], value["id"])
        self.audio_status.setText(f"Wykryto {len(values)} źródeł. Wybierz urządzenia i przetestuj poziom przed nagraniem.")

    def source_selection(self):
        selected = [(self.mic.currentData(), self.gains[0].value()),
                    (self.system.currentData(), self.gains[1].value())]
        selected = [(device, gain) for device, gain in selected if device]
        if not selected:
            raise ValueError("Najpierw wykryj i wybierz źródło audio.")
        if len({value[0] for value in selected}) != len(selected):
            raise ValueError("Wybierz dwa różne źródła lub wyłącz jedno wejście.")
        return [value[0] for value in selected], [value[1] for value in selected]

    def choose_audio_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Katalog nagrań", self.audio_dir.text())
        if path:
            self.audio_dir.setText(path)

    def create_recorder(self, test=False):
        from .audio import Recorder
        ids, gains = self.source_selection()
        path = Path(self.audio_dir.text()).expanduser() / f"spotkanie-{time.time_ns()}.wav"
        recorder = Recorder(path, ids, split=self.mix.currentIndex() == 1, gains=gains, test=test)
        recorder.start()
        self.recorder = recorder
        self.owner.recorder = recorder
        self.owner.last_marker_id = None
        if not test:
            self.record_entry = recorder.metadata()
            self.owner.meeting.recordings.append(self.record_entry)
            self.owner.schedule_save()

    def test_sources(self):
        if not self.recorder or not self.recorder.active:
            try:
                self.create_recorder(test=True)
            except (ValueError, OSError) as exc:
                self.show_error(str(exc))

    def start_recording(self):
        if self.recorder and self.recorder.active:
            return
        if QMessageBox.question(self, "Rozpocząć nagranie?", "Nagranie obejmie wybrane źródła audio. Upewnij się, że uczestnicy zostali poinformowani i możesz nagrywać to spotkanie. Plik pozostanie lokalnie.") != QMessageBox.StandardButton.Yes:
            return
        try:
            self.create_recorder()
        except (ValueError, OSError) as exc:
            self.show_error(str(exc))

    def stop_recording(self):
        if self.recorder:
            self.recorder.stop()
            self.audio_status.setText("Zatrzymywanie — trwa zamykanie pliku. Poczekaj przed wyjściem.")

    def pause_recording(self):
        if self.recorder:
            if self.recorder.pause_event.is_set():
                self.recorder.pause_event.clear()
            else:
                self.recorder.pause_event.set()

    def switch_segment(self):
        if self.recorder and self.recorder.active and not self.recorder.test:
            if QMessageBox.question(self, "Nowy segment", "Zamknąć obecny plik i rozpocząć nowy z obecnie wybranymi źródłami? Między segmentami wystąpi krótka przerwa.") == QMessageBox.StandardButton.Yes:
                try:
                    self.source_selection()
                except ValueError as exc:
                    self.show_error(str(exc))
                    return
                self.pending_restart = True
                self.stop_recording()

    def poll(self):
        active = bool(self.recorder and self.recorder.active)
        for widget in (self.start, self.test):
            widget.setEnabled(not active)
        for widget in (self.pause, self.stop, self.segment):
            widget.setEnabled(active)
        self.send.setEnabled(not self.transcribing)
        self.cancel.setEnabled(self.transcribing)
        self.transcript_text.setReadOnly(self.transcribing)
        if not self.recorder:
            return
        recorder = self.recorder
        self.level.setValue(int(min(1, max(recorder.levels, default=0)) * 100))
        if self.record_entry and not recorder.test:
            self.record_entry.update(recorder.metadata())
        if active:
            status = "Test audio" if recorder.test else "Pauza nagrania" if recorder.pause_event.is_set() else "● NAGRYWANIE"
            text = f"{status} {format_time(recorder.seconds)}"
            self.owner.recording_label.setText(text)
            self.owner.tray.setToolTip((text + " · " + self.owner.plan_label.text())[:120])
            self.audio_status.setText(text + (" · otwieranie źródeł…" if not recorder.ready else " · plik lokalny"))
            self.pause.setText("Wznów nagranie" if recorder.pause_event.is_set() else "Pauza nagrania")
        else:
            self.owner.recording_label.setText("")
            self.owner.recorder = None
            self.recorder = None
            if recorder.error:
                self.pending_restart = False
                self.show_error(recorder.error)
            elif recorder.test:
                self.audio_status.setText("Test zakończony. Nie zapisano dźwięku. W razie ciszy sprawdź wybrane źródła.")
            else:
                self.last_recording = recorder.path
                self.audio_file.setText(str(recorder.path))
                self.audio_status.setText(f"Zapisano lokalnie: {recorder.path.name}")
            self.record_entry = None
            self.owner.schedule_save()
            if self.pending_restart:
                self.pending_restart = False
                try:
                    self.create_recorder()
                except (ValueError, OSError) as exc:
                    self.show_error(str(exc))

    def choose_audio_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Zakończone nagranie", self.audio_dir.text(), "Audio (*.wav *.mp3 *.m4a *.mp4 *.webm *.mpeg *.mpga)")
        if path:
            self.audio_file.setText(path)

    def keyring_operation(self, operation):
        try:
            import keyring
            backend = keyring.get_keyring()
            name = f"{type(backend).__module__}.{type(backend).__name__}".lower()
            if any(term in name for term in ("plaintext", "fail", "null", "chainer")):
                raise ValueError("Brak bezpiecznego systemowego magazynu. Klucz pozostaje tylko w sesji.")
            return operation(keyring)
        except Exception:
            self.show_error("Magazyn poświadczeń jest niedostępny. Użyj klucza tylko w bieżącej sesji; nie zapisujemy go do pliku.")
            return None

    def load_key(self):
        value = self.keyring_operation(lambda k: k.get_password("licznik-spotkaniowy", "openai"))
        if value:
            self.api_key.setText(value)

    def save_key(self):
        key = self.api_key.text().strip()
        if not key:
            return
        self.keyring_operation(lambda k: k.set_password("licznik-spotkaniowy", "openai", key))

    def delete_key(self):
        self.api_key.clear()
        self.keyring_operation(lambda k: k.delete_password("licznik-spotkaniowy", "openai"))

    def transcribe(self):
        if self.transcribing:
            return
        path = Path(self.audio_file.text()).expanduser()
        if self.recorder and self.recorder.active and path == self.recorder.path:
            self.show_error("Najpierw zakończ nagranie i poczekaj na zapis pliku.")
            return
        key = self.api_key.text().strip()
        if not key:
            self.show_error("Wpisz własny klucz OpenAI API.")
            return
        try:
            info = inspect_audio(path)
        except (OSError, ValueError) as exc:
            self.show_error(str(exc))
            return
        message = (f"Dostawca: OpenAI · model: {MODEL}\nPlik: {path.name}\n"
                   f"Rozmiar: {path.stat().st_size / 1_000_000:.1f} MB · żądania: {info['parts']}\n\n"
                   "Do api.openai.com zostanie wysłane wyłącznie audio, klucz i parametry techniczne. "
                   "Nagrania WAV dzielimy na fragmenty do 5 minut. Usługa może naliczyć opłaty "
                   "na Twoim koncie API. Notatki i agenda pozostaną lokalnie. Anulowanie nie cofnie "
                   "przesłanych danych ani kosztów.\n\nWysłać nagranie?")
        if QMessageBox.question(self, "Potwierdź wysyłkę audio", message) != QMessageBox.StandardButton.Yes:
            return
        self.transcribing = True
        self.transcriber = Transcriber()
        self.transcript_entry = {"source": str(path), "model": MODEL, "text": "", "parts": [], "complete": False}
        entry = self.transcript_entry
        self.owner.meeting.transcripts.append(entry)
        self.transcript_choice.addItem(f"{len(self.owner.meeting.transcripts)}. {path.name}")
        self.transcript_choice.setCurrentIndex(len(self.owner.meeting.transcripts) - 1)
        self.transcript_choice.setEnabled(False)
        self.transcript_text.clear()
        self.api_status.setText("Przygotowanie i wysyłanie… bez automatycznych powtórzeń")
        transcriber = self.transcriber
        output = self.owner.directory / "transcripts" / f"transcript-{time.time_ns()}.json"
        self.owner.schedule_save()
        def operation():
            parts = []
            cache = self.owner.directory / ".transcription-cache"
            cache.mkdir(mode=0o700, parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="job-", dir=cache) as temporary:
                chunks = wav_chunks(path, temporary, transcriber.cancelled) if info["wav"] else [(path, 0)]
                for chunk, offset in chunks:
                    result = transcriber.upload(chunk, key)
                    parts.append({"offset": offset, **result})
                    atomic_json(output, {"source": str(path), "model": MODEL, "parts": parts,
                                         "text": "\n\n".join(part["text"] for part in parts), "complete": False})
                value = {"source": str(path), "model": MODEL, "parts": parts,
                         "text": "\n\n".join(part["text"] for part in parts), "complete": True}
                atomic_json(output, value)
                return value
        self.run_worker(operation, self.transcribed, self.transcription_error)
        self.partial_output = output

    def transcribed(self, result):
        self.transcribing = False
        self.transcript_choice.setEnabled(True)
        self.transcriber = None
        self.transcript_entry.update(result)
        self.transcript_text.setPlainText(result["text"])
        self.api_status.setText("Gotowe · fragmenty bez znaczników API nie są automatycznie przypisywane do punktów.")
        self.owner.schedule_save()

    def transcription_error(self, text):
        self.transcribing = False
        self.transcript_choice.setEnabled(True)
        self.transcriber = None
        if self.partial_output.exists():
            from .storage import read_json
            try:
                result = read_json(self.partial_output)
                self.transcript_entry.update(result)
                self.transcript_text.setPlainText(result["text"])
            except (OSError, ValueError, KeyError):
                pass
        self.api_status.setText("Zadanie niedokończone. Zachowano odebrane fragmenty; nie ponowiono żądania.")
        self.owner.schedule_save()
        self.show_error(text)

    def cancel_transcription(self):
        if self.transcriber:
            self.transcriber.cancel()
            self.api_status.setText("Anulowanie… trwa kończenie bieżącego zadania.")

    def edit_transcript(self):
        if not self.transcribing and self.transcript_entry:
            self.transcript_entry["text"] = self.transcript_text.toPlainText()
            self.owner.schedule_save()

    def assign_transcript(self):
        item = self.owner.selected_item()
        if self.transcript_entry and item and not self.transcribing:
            self.transcript_entry["item_id"] = item.id
            self.api_status.setText(f"Ręcznie przypisano do: {item.title}")
            self.owner.schedule_save()

    def export_transcript(self):
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz transkrypcję", "transkrypcja.txt", "Tekst (*.txt)")
        if path:
            try:
                Path(path).write_text(self.transcript_text.toPlainText(), encoding="utf-8")
            except OSError:
                self.show_error("Nie udało się zapisać transkrypcji.")


def owner_path(owner):
    return owner.directory
