import json
import threading
import wave

import pytest

from meeting_timer.transcription import Cancelled, Transcriber, inspect_audio, wav_chunks


class Response:
    status = 200

    def read(self, limit):
        return json.dumps({"text": "Zażółć gęślą jaźń"}).encode()


class Connection:
    sock = None

    def __init__(self, status=200):
        self.headers, self.data, self.requests = {}, [], []
        self.status = status

    def putrequest(self, *args):
        self.requests.append(args)

    def putheader(self, key, value):
        self.headers[key] = value

    def endheaders(self):
        pass

    def send(self, data):
        self.data.append(data)

    def getresponse(self):
        result = Response()
        result.status = self.status
        return result

    def close(self):
        pass


def test_upload_stream_and_generic_filename(tmp_path):
    path = tmp_path / "prywatny-klient.mp3"
    path.write_bytes(b"audio" * 40_000)
    connection = Connection()
    result = Transcriber(lambda: connection).upload(path, "test-secret")
    assert result["text"] == "Zażółć gęślą jaźń"
    body = b"".join(connection.data)
    assert b"prywatny-klient" not in body
    assert b"test-secret" not in body
    assert connection.headers["Authorization"] == "Bearer test-secret"
    assert int(connection.headers["Content-Length"]) == len(body)
    assert len(connection.requests) == 1
    assert max(map(len, connection.data)) <= 65536


@pytest.mark.parametrize("status", [401, 403, 413, 429, 500])
def test_api_error_no_retry(tmp_path, status):
    path = tmp_path / "a.mp3"
    path.write_bytes(b"abc")
    connection = Connection(status)
    with pytest.raises(ValueError):
        Transcriber(lambda: connection).upload(path, "secret")
    assert len(connection.requests) == 1


def test_cancel_before_send(tmp_path):
    connection = Connection()
    client = Transcriber(lambda: connection)
    client.cancel()
    with pytest.raises(Cancelled):
        client.upload(tmp_path / "not-even-present.wav", "secret")
    assert not connection.requests


def test_wav_chunk_downsample(tmp_path):
    pytest.importorskip("numpy")
    source = tmp_path / "input.wav"
    with wave.open(str(source), "wb") as output:
        output.setparams((2, 2, 48000, 0, "NONE", "none"))
        output.writeframes(b"\0\0" * 48000 * 2 * 2)
    info = inspect_audio(source)
    assert info == {"seconds": 2, "parts": 1, "wav": True}
    chunks = wav_chunks(source, tmp_path, threading.Event())
    chunk, offset = next(chunks)
    with wave.open(str(chunk), "rb") as output:
        assert output.getframerate() == 16000
        assert output.getnframes() == 32000
        assert output.getnchannels() == 1
    assert offset == 0
    assert list(chunks) == []
    assert not chunk.exists()


def test_recording_pause_and_markers(tmp_path):
    np = pytest.importorskip("numpy")
    from meeting_timer.audio import BLOCK, Recorder
    recorder = None

    class Source:
        calls = 0

        def recorder(self, **kwargs):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def record(self, numframes):
            self.calls += 1
            if self.calls == 1:
                recorder.mark("point-id", "Tytuł")
                recorder.pause_event.set()
            elif self.calls == 2:
                recorder.pause_event.clear()
            else:
                recorder.stop()
            return np.ones((numframes, 2), dtype="float32") * 0.1

    path = tmp_path / "recording.wav"
    recorder = Recorder(path, ["synthetic"], source_factory=lambda ids: [Source()])
    recorder.start()
    recorder.thread.join(3)
    assert not recorder.active
    assert not recorder.error
    with wave.open(str(path), "rb") as audio:
        assert audio.getnframes() == 2 * BLOCK
    assert recorder.markers[0]["item_id"] == "point-id"
    assert recorder.markers[0]["seconds"] == 0
    assert path.with_suffix(".markers.json").exists()
