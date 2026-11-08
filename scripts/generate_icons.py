"""Render our SVG to native launcher icons using the existing Qt dependency."""

import os
import struct
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).resolve().parents[1] / "meeting_timer/assets"


def main():
    app = QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(ASSETS / "app.svg"))

    def png(size):
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        assert image.save(buffer, "PNG")
        return bytes(buffer.data())

    sizes = (16, 32, 48, 64, 128, 256)
    frames = [png(size) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(sizes))
    offset = len(header) + 16 * len(sizes)
    entries = []
    for size, data in zip(sizes, frames):
        entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    (ASSETS / "app.ico").write_bytes(header + b"".join(entries) + b"".join(frames))
    chunks = []
    for tag, size in ((b"ic07", 128), (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024)):
        data = png(size)
        chunks.append(tag + struct.pack(">I", len(data) + 8) + data)
    body = b"".join(chunks)
    (ASSETS / "app.icns").write_bytes(b"icns" + struct.pack(">I", len(body) + 8) + body)
    (ASSETS / "app.png").write_bytes(png(256))
    app.quit()


if __name__ == "__main__":
    main()
