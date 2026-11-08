"""Platform-specific API checks; synthetic native messages, no real user input."""

import ctypes as C
import sys

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from meeting_timer.global_hotkeys import MacBackend, WindowsBackend


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows native API only')
def test_windows_registration_thread_message_conflict_and_release():
    app = QApplication.instance() or QApplication([])
    received = []
    backend = WindowsBackend(received.append)
    other = WindowsBackend(lambda _name: None)
    try:
        backend.register('next', 'Ctrl+Alt+Shift+F19')
        with pytest.raises(ValueError):
            other.register('conflict', 'Ctrl+Alt+Shift+F19')
        with pytest.raises(ValueError):
            other.register('reserved', 'Ctrl+Alt+Shift+F12')
        identifier = next(iter(backend.handles))
        kernel = C.WinDLL('kernel32')
        kernel.GetCurrentThreadId.restype = C.c_uint32
        backend.user32.PostThreadMessageW.argtypes = [C.c_uint32, C.c_uint32, C.c_size_t, C.c_ssize_t]
        assert backend.user32.PostThreadMessageW(kernel.GetCurrentThreadId(), 0x0312, identifier, 0)
        for _ in range(10):
            app.processEvents()
            if received:
                break
            QTest.qWait(10)
        assert received == ['next']
        backend.clear()
        other.register('released', 'Ctrl+Alt+Shift+F19')
    finally:
        backend.close()
        other.close()


@pytest.mark.skipif(sys.platform != 'darwin', reason='macOS native API only')
def test_mac_carbon_registration_layout_callback_and_release():
    app = QApplication.instance() or QApplication([])
    received = []
    backend = MacBackend(received.append)
    try:
        backend.register('next', 'Ctrl+Alt+Shift+N')
        identifier = next(iter(backend.handles))
        c = backend.carbon
        c.CreateEvent.argtypes = [C.c_void_p, C.c_uint32, C.c_uint32, C.c_double,
                                 C.c_uint32, C.POINTER(C.c_void_p)]
        c.CreateEvent.restype = C.c_int32
        c.SetEventParameter.argtypes = [C.c_void_p, C.c_uint32, C.c_uint32, C.c_uint32, C.c_void_p]
        c.SetEventParameter.restype = C.c_int32
        c.SendEventToEventTarget.argtypes = [C.c_void_p, C.c_void_p]
        c.SendEventToEventTarget.restype = C.c_int32
        c.ReleaseEvent.argtypes = [C.c_void_p]
        for kind in (5, 5, 6, 5, 6):
            event = C.c_void_p()
            assert c.CreateEvent(None, 0x6B657962, kind, 0, 0, C.byref(event)) == 0
            try:
                identity = backend.HotKeyID(0x4D544D52, identifier)
                assert c.SetEventParameter(event, 0x2D2D2D2D, 0x686B6964,
                                           C.sizeof(identity), C.byref(identity)) == 0
                assert c.SendEventToEventTarget(event, c.GetApplicationEventTarget()) == 0
            finally:
                c.ReleaseEvent(event)
        app.processEvents()
        assert received == ['next', 'next']  # Press repeat did not trigger an extra action.
        backend.clear()
        backend.register('released', 'Ctrl+Alt+Shift+N')
    finally:
        backend.close()
