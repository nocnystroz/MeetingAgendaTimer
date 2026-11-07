"""Optional SoundCard backend. Imports native audio and numpy only on use."""

import os
import threading
import time
import wave
from contextlib import ExitStack
from pathlib import Path

from .storage import atomic_json

RATE = 48000
BLOCK = 4800


def devices():
    import soundcard as sc
    return [{"id": str(m.id), "name": m.name, "loopback": bool(m.isloopback)}
            for m in sc.all_microphones(include_loopback=True)]


def native_sources(ids):
    import soundcard as sc
    return [sc.get_microphone(id=value, include_loopback=True) for value in ids]


class Recorder:
    def __init__(self, path, ids, split=False, gains=None, source_factory=native_sources, test=False):
        self.path = Path(path)
        self.ids = ids
        self.split = split
        self.gains = gains or [1.0] * len(ids)
        self.source_factory = source_factory
        self.test = test
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread = None
        self.frames = 0
        self.levels = []
        self.error = ""
        self.markers = []
        self.lock = threading.Lock()
        self.started_at = time.time()
        self.ready = False

    @property
    def active(self):
        return self.thread is not None and self.thread.is_alive()

    @property
    def seconds(self):
        return self.frames / RATE

    def start(self):
        if not self.ids or len(self.ids) > 2:
            raise ValueError("Wybierz jedno lub dwa źródła audio.")
        if self.path.exists():
            raise ValueError("Plik nagrania już istnieje.")
        self.thread = threading.Thread(target=self._run, name="meeting-audio", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def mark(self, item_id, title):
        with self.lock:
            self.markers.append({"item_id": item_id, "title": title, "seconds": self.seconds})

    def metadata(self):
        with self.lock:
            return {"path": str(self.path), "seconds": self.seconds,
                    "started_at": self.started_at, "markers": list(self.markers),
                    "channels": len(self.ids) if self.split else 1,
                    "error": bool(self.error)}

    def _run(self):
        try:
            import numpy as np
            sources = self.source_factory(self.ids)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with ExitStack() as stack:
                streams = [stack.enter_context(source.recorder(samplerate=RATE, blocksize=BLOCK))
                           for source in sources]
                output = None
                if not self.test:
                    fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    raw_file = stack.enter_context(os.fdopen(fd, "wb"))
                    output = stack.enter_context(wave.open(raw_file, "wb"))
                    output.setnchannels(len(sources) if self.split else 1)
                    output.setsampwidth(2)
                    output.setframerate(RATE)
                self.ready = True
                while not self.stop_event.is_set():
                    # Stereo input averaged to mono avoids WASAPI single-channel capture issues.
                    chunks = [stream.record(numframes=BLOCK).mean(axis=1) * gain
                              for stream, gain in zip(streams, self.gains)]
                    self.levels = [float(np.max(np.abs(chunk))) for chunk in chunks]
                    if self.pause_event.is_set():
                        continue  # Drain input; paused samples never enter the output file.
                    if self.split:
                        audio = np.column_stack(chunks)
                    else:
                        audio = sum(chunks) / len(chunks)
                    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
                    if output:
                        # writeframes updates the WAV length each block, aiding crash recovery.
                        output.writeframes(pcm)
                    self.frames += len(chunks[0])
                    if self.seconds >= 3 and self.test:
                        break
                    if not self.test and self.frames % RATE == 0:
                        atomic_json(self.path.with_suffix(".markers.json"), self.metadata())
                    if self.frames * 2 * (len(sources) if self.split else 1) > 3_800_000_000:
                        self.error = "Osiągnięto limit segmentu WAV. Rozpocznij kolejne nagranie."
                        break
        except Exception:
            # Backend exceptions may contain private device IDs. Keep them out of logs/UI.
            self.error = "Błąd audio. Sprawdź urządzenia, uprawnienia, wolne miejsce i dostępność systemu dźwięku. Zapisana część pliku pozostaje na dysku."
        finally:
            if not self.test and self.path.exists():
                try:
                    atomic_json(self.path.with_suffix(".markers.json"), self.metadata())
                except OSError:
                    self.error = "Nie udało się zapisać znaczników. Sprawdź wolne miejsce."
