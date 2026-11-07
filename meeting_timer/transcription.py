"""Explicit, cancellable streamed HTTPS upload. No retries, SDK or local model."""

import http.client
import json
import math
import socket
import ssl
import threading
import uuid
import wave
from pathlib import Path

MAX_UPLOAD = 24_000_000
MODEL = "gpt-transcribe"
ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"


class Cancelled(Exception):
    pass


def inspect_audio(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError("Wybierz niepusty plik nagrania.")
    if path.suffix.lower() not in (".wav", ".mp3", ".m4a", ".mp4", ".webm", ".mpeg", ".mpga"):
        raise ValueError("Nieobsługiwany format nagrania.")
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as source:
                if source.getsampwidth() != 2 or source.getframerate() not in (16000, 48000):
                    raise ValueError("WAV musi być PCM 16-bit, 16 lub 48 kHz. Użyj nagrania z aplikacji lub przekonwertuj plik.")
                duration = source.getnframes() / source.getframerate()
                if duration <= 0:
                    raise ValueError("Nagranie jest puste.")
                return {"seconds": duration, "parts": max(1, math.ceil(duration / 300)), "wav": True}
        except (wave.Error, EOFError) as exc:
            raise ValueError("Nie można odczytać pliku WAV.") from exc
    if path.stat().st_size > MAX_UPLOAD:
        raise ValueError("Ten plik przekracza 24 MB. Długie nagrania dzielimy automatycznie tylko dla WAV z aplikacji.")
    return {"seconds": None, "parts": 1, "wav": False}


def wav_chunks(path, directory, cancelled):
    """Stream convert our PCM WAV to 5-minute 16 kHz mono pieces (~9.6 MB)."""
    import numpy as np
    with wave.open(str(path), "rb") as source:
        rate, channels = source.getframerate(), source.getnchannels()
        index = 0
        while source.tell() < source.getnframes():
            if cancelled.is_set():
                raise Cancelled()
            offset = source.tell() / rate
            target = Path(directory) / f"part-{index:04}.wav"
            with wave.open(str(target), "wb") as output:
                output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                remaining = rate * 300
                while remaining > 0:
                    if cancelled.is_set():
                        raise Cancelled()
                    raw = source.readframes(min(rate, remaining))
                    if not raw:
                        break
                    values = np.frombuffer(raw, dtype="<i2").reshape(-1, channels).mean(axis=1)
                    if rate == 48000:
                        padded = values[:len(values) // 3 * 3]
                        values = padded.reshape(-1, 3).mean(axis=1)
                    output.writeframes(values.astype("<i2").tobytes())
                    remaining -= len(raw) // (channels * 2)
            yield target, offset
            target.unlink(missing_ok=True)
            index += 1


class Transcriber:
    def __init__(self, connection_factory=None):
        self.cancelled = threading.Event()
        self.connection = None
        self.connection_factory = connection_factory

    def cancel(self):
        self.cancelled.set()
        connection = self.connection
        if connection:
            try:
                if connection.sock:
                    connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()

    def upload(self, path, key, model=MODEL, progress=lambda sent, total: None):
        if self.cancelled.is_set():
            raise Cancelled()
        path = Path(path)
        key = key.strip()
        if not key or any(not 33 <= ord(c) <= 126 for c in key):
            raise ValueError("Wpisz poprawny klucz API.")
        if path.stat().st_size > MAX_UPLOAD:
            raise ValueError("Plik przekracza limit wysyłki 24 MB.")
        boundary = "meeting" + uuid.uuid4().hex
        prefix = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n"
                  f"{model}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                  f"filename=\"audio{path.suffix.lower()}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode()
        suffix = f"\r\n--{boundary}--\r\n".encode()
        total = len(prefix) + path.stat().st_size + len(suffix)
        if self.connection_factory:
            connection = self.connection_factory()
        else:
            import certifi
            connection = http.client.HTTPSConnection("api.openai.com", timeout=90,
                          context=ssl.create_default_context(cafile=certifi.where()))
        self.connection = connection
        try:
            connection.putrequest("POST", "/v1/audio/transcriptions")
            connection.putheader("Authorization", "Bearer " + key.strip())
            connection.putheader("Content-Type", "multipart/form-data; boundary=" + boundary)
            connection.putheader("Content-Length", str(total))
            connection.endheaders()
            connection.send(prefix)
            sent = len(prefix)
            with path.open("rb") as stream:
                while chunk := stream.read(64 * 1024):
                    if self.cancelled.is_set():
                        raise Cancelled()
                    connection.send(chunk)
                    sent += len(chunk)
                    progress(sent, total)
            if self.cancelled.is_set():
                raise Cancelled()
            connection.send(suffix)
            response = connection.getresponse()
            payload = response.read(8 * 1024 * 1024 + 1)
            if self.cancelled.is_set():
                raise Cancelled()
            if response.status != 200:
                explanations = {401: "Błędny klucz API.", 403: "Brak dostępu do usługi.",
                                413: "Plik jest za duży.", 429: "Limit API lub środków na koncie."}
                raise ValueError(explanations.get(response.status, "Usługa zwróciła błąd. Sprawdź konto API. Nie ponowiono wysyłki."))
            if len(payload) > 8 * 1024 * 1024:
                raise ValueError("Odpowiedź API jest zbyt duża.")
            result = json.loads(payload)
            if not isinstance(result, dict) or not isinstance(result.get("text"), str):
                raise ValueError("Nieprawidłowa odpowiedź API.")
            return {"text": result["text"], "segments": result.get("segments", [])}
        except (OSError, http.client.HTTPException) as exc:
            if self.cancelled.is_set():
                raise Cancelled() from None
            raise ValueError("Błąd sieci lub timeout. Nie ponowiono wysyłki; zlecenie mogło zostać naliczone.") from exc
        finally:
            connection.close()
            self.connection = None
