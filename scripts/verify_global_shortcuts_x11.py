"""Manual integration check on an X11 desktop; xdotool/xmessage required."""

import os
import subprocess
import tempfile

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from meeting_timer.global_hotkeys import X11Backend
from meeting_timer.model import Item
from meeting_timer.windows import MainWindow


def main():
    previous = subprocess.check_output(["xdotool", "getactivewindow"], text=True).strip()
    app = QApplication([])
    assert app.platformName() == "xcb", "Run with QT_QPA_PLATFORM=xcb on an X11 desktop."
    with tempfile.TemporaryDirectory(prefix="meeting-global-x11-") as folder:
        os.environ["MEETING_TIMER_DATA_DIR"] = folder
        window = MainWindow()
        window.tick_timer.stop()
        manager = window.shortcuts.global_hotkeys
        presentation = None
        try:
            assert not manager.errors, manager.status()
            assert len(manager.registered) == 6, manager.registered
            window.replace_items([Item("Synthetic point A", 300), Item("Synthetic point B", 600)])
            window.engine.start()
            window.engine.toggle_pause()
            presentation = subprocess.Popen(
                [
                    "xmessage",
                    "-title",
                    "Synthetic Meeting Presentation",
                    "-buttons",
                    "Close",
                    "Synthetic presentation for global-hotkey test. No real recording.",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(30):
                found = subprocess.run(
                    ["xdotool", "search", "--name", "^Synthetic Meeting Presentation$"],
                    capture_output=True,
                    text=True,
                )
                if found.returncode == 0:
                    break
                QTest.qWait(100)
            assert found.returncode == 0
            target = found.stdout.splitlines()[-1]
            subprocess.run(["xdotool", "windowactivate", "--sync", target], check=True)
            QTest.qWait(200)

            def press(function):
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", f"ctrl+alt+shift+{function}"], check=True
                )
                QTest.qWait(200)
                active = subprocess.check_output(["xdotool", "getactivewindow"], text=True).strip()
                assert active == target, (active, target)

            press("n")
            assert window.engine.snapshot().index == 1
            press("b")
            assert window.engine.snapshot().index == 0
            before = window.meeting.items[0].seconds
            press("u")
            assert window.meeting.items[0].seconds == before + 60
            press("i")
            assert window.meeting.items[0].seconds == before + 360
            window.shortcuts.extra_minutes = 3
            press("o")
            assert window.meeting.items[0].seconds == before + 540
            press("p")
            assert not window.engine.paused
            press("p")
            assert window.engine.paused
            rival = X11Backend(lambda _name: None)
            try:
                try:
                    rival.register("rival", "Ctrl+Alt+Shift+N")
                except ValueError:
                    pass
                else:
                    raise AssertionError("Expected native registration conflict")
            finally:
                rival.close()
            press("n")
            assert window.engine.snapshot().index == 1
            manager.close()
            probe = X11Backend(lambda _name: None)
            probe.register("released", "Ctrl+Alt+Shift+N")
            probe.close()
            print(
                "PASS: next, previous, +1, +5, custom +3, pause/resume while another process has focus; focus preserved; native conflict detected; keys released."
            )
        finally:
            manager.close()
            window.save_timer.stop()
            window.tray.hide()
            window.hide()
            if presentation:
                presentation.terminate()
                presentation.wait(timeout=5)
            subprocess.run(
                ["xdotool", "windowactivate", previous],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


if __name__ == "__main__":
    main()
