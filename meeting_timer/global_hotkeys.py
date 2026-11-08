"""Native hotkey registration; no keyboard hooks, polling, input capture or network."""

import ctypes as C
import itertools
import os
import sys
from ctypes.util import find_library

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, QSocketNotifier, Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication

from .i18n import tr

GLOBAL_DEFAULTS = {
    'previous': 'Ctrl+Alt+Shift+B', 'next': 'Ctrl+Alt+Shift+N',
    'play': 'Ctrl+Alt+Shift+P', 'add_minute': 'Ctrl+Alt+Shift+U',
    'add_five': 'Ctrl+Alt+Shift+I', 'add_custom': 'Ctrl+Alt+Shift+O',
}
_IDS = itertools.count(0x2000)


def combination(value):
    sequence = QKeySequence(value, QKeySequence.SequenceFormat.PortableText)
    if sequence.count() != 1:
        raise ValueError(tr('Nieobsługiwany skrót globalny.'))
    key = sequence[0]
    return int(key.key()), key.keyboardModifiers()


def native_modifiers(modifiers, control, alt, shift, meta):
    result = 0
    for flag, mask in [(Qt.KeyboardModifier.ControlModifier, control),
                       (Qt.KeyboardModifier.AltModifier, alt),
                       (Qt.KeyboardModifier.ShiftModifier, shift),
                       (Qt.KeyboardModifier.MetaModifier, meta)]:
        if modifiers & flag:
            result |= mask
    return result


class WindowsBackend(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        from ctypes import wintypes as W
        self.W = W
        self.callback = callback
        self.handles = {}
        self.user32 = C.WinDLL('user32', use_last_error=True)
        self.user32.RegisterHotKey.argtypes = [W.HWND, C.c_int, W.UINT, W.UINT]
        self.user32.RegisterHotKey.restype = W.BOOL
        self.user32.UnregisterHotKey.argtypes = [W.HWND, C.c_int]
        self.user32.UnregisterHotKey.restype = W.BOOL
        self.user32.VkKeyScanW.argtypes = [W.WCHAR]
        self.user32.VkKeyScanW.restype = C.c_short
        QApplication.instance().installNativeEventFilter(self)

    def register(self, name, value):
        key, modifiers = combination(value)
        extra = 0
        special = {int(Qt.Key.Key_Left): 0x25, int(Qt.Key.Key_Right): 0x27,
                   int(Qt.Key.Key_Up): 0x26, int(Qt.Key.Key_Down): 0x28,
                   int(Qt.Key.Key_PageUp): 0x21, int(Qt.Key.Key_PageDown): 0x22,
                   int(Qt.Key.Key_Home): 0x24, int(Qt.Key.Key_End): 0x23,
                   int(Qt.Key.Key_Return): 0x0D, int(Qt.Key.Key_Enter): 0x0D,
                   int(Qt.Key.Key_Space): 0x20, int(Qt.Key.Key_Escape): 0x1B}
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
            vk = 0x70 + key - int(Qt.Key.Key_F1)
        elif key in special:
            vk = special[key]
        elif 48 <= key <= 57 or 65 <= key <= 90:
            vk = key
        elif 0 < key < 0x10000:
            mapped = self.user32.VkKeyScanW(chr(key))
            if mapped == -1:
                raise ValueError(tr('Nieobsługiwany skrót globalny.'))
            vk = mapped & 0xFF
            extra = ((mapped >> 8) & 1) * 4 | ((mapped >> 8) & 2) | (((mapped >> 8) & 4) >> 2)
        else:
            raise ValueError(tr('Nieobsługiwany skrót globalny.'))
        if vk == 0x7B:
            raise ValueError(tr('F12 jest zarezerwowany przez Windows.'))
        identifier = next(_IDS)
        flags = native_modifiers(modifiers, 2, 1, 4, 8) | extra | 0x4000
        if not self.user32.RegisterHotKey(None, identifier, flags, vk):
            raise ValueError(tr('Skrót zajęty lub zablokowany przez system.'))
        self.handles[identifier] = name

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (b'windows_generic_MSG', b'windows_dispatcher_MSG'):
            msg = self.W.MSG.from_address(int(message))
            if msg.message == 0x0312 and int(msg.wParam) in self.handles:
                self.callback(self.handles[int(msg.wParam)])
                return True, 0
        return False, 0

    def clear(self):
        for identifier in self.handles:
            self.user32.UnregisterHotKey(None, identifier)
        self.handles.clear()

    def close(self):
        self.clear()
        QApplication.instance().removeNativeEventFilter(self)


class MacBackend:
    class HotKeyID(C.Structure):
        _fields_ = [('signature', C.c_uint32), ('id', C.c_uint32)]

    class EventType(C.Structure):
        _fields_ = [('eventClass', C.c_uint32), ('eventKind', C.c_uint32)]

    def __init__(self, callback):
        self.callback = callback
        self.handles = {}
        self.pressed = set()
        self.carbon = C.CDLL('/System/Library/Frameworks/Carbon.framework/Carbon')
        c = self.carbon
        c.GetApplicationEventTarget.restype = C.c_void_p
        c.RegisterEventHotKey.argtypes = [C.c_uint32, C.c_uint32, self.HotKeyID,
                                         C.c_void_p, C.c_uint32, C.POINTER(C.c_void_p)]
        c.RegisterEventHotKey.restype = C.c_int32
        c.UnregisterEventHotKey.argtypes = [C.c_void_p]
        c.UnregisterEventHotKey.restype = C.c_int32
        c.GetEventKind.argtypes = [C.c_void_p]
        c.GetEventKind.restype = C.c_uint32
        c.GetEventParameter.argtypes = [C.c_void_p, C.c_uint32, C.c_uint32,
                                       C.c_void_p, C.c_uint32, C.c_void_p, C.c_void_p]
        c.GetEventParameter.restype = C.c_int32
        callback_type = C.CFUNCTYPE(C.c_int32, C.c_void_p, C.c_void_p, C.c_void_p)
        self.handler = callback_type(self.handle_event)
        c.InstallEventHandler.argtypes = [C.c_void_p, callback_type, C.c_uint32,
                                         C.POINTER(self.EventType), C.c_void_p, C.POINTER(C.c_void_p)]
        c.InstallEventHandler.restype = C.c_int32
        c.RemoveEventHandler.argtypes = [C.c_void_p]
        c.RemoveEventHandler.restype = C.c_int32
        self.handler_ref = C.c_void_p()
        event_types = (self.EventType * 2)(self.EventType(0x6B657962, 5), self.EventType(0x6B657962, 6))
        if c.InstallEventHandler(c.GetApplicationEventTarget(), self.handler, 2, event_types,
                                 None, C.byref(self.handler_ref)) != 0:
            raise OSError(tr('Nie można uruchomić skrótów globalnych.'))
        self.layout_keys = None

    def character_keys(self):
        # Translate the current macOS keyboard layout instead of assuming ANSI/QWERTY.
        c = self.carbon
        cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        c.TISCopyCurrentASCIICapableKeyboardLayoutInputSource.restype = C.c_void_p
        c.TISGetInputSourceProperty.argtypes = [C.c_void_p, C.c_void_p]
        c.TISGetInputSourceProperty.restype = C.c_void_p
        cf.CFDataGetBytePtr.argtypes = [C.c_void_p]
        cf.CFDataGetBytePtr.restype = C.c_void_p
        cf.CFRelease.argtypes = [C.c_void_p]
        c.UCKeyTranslate.argtypes = [C.c_void_p, C.c_uint16, C.c_uint16, C.c_uint32,
                                    C.c_uint32, C.c_uint32, C.POINTER(C.c_uint32), C.c_uint32,
                                    C.POINTER(C.c_uint32), C.POINTER(C.c_uint16)]
        c.UCKeyTranslate.restype = C.c_int32
        source = c.TISCopyCurrentASCIICapableKeyboardLayoutInputSource()
        result = {}
        if not source:
            return result
        try:
            property_key = C.c_void_p.in_dll(c, 'kTISPropertyUnicodeKeyLayoutData')
            layout_data = c.TISGetInputSourceProperty(source, property_key)
            if not layout_data:
                return result
            layout = cf.CFDataGetBytePtr(layout_data)
            for native in range(128):
                state, length = C.c_uint32(), C.c_uint32()
                chars = (C.c_uint16 * 8)()
                if c.UCKeyTranslate(layout, native, 0, 0, 0, 1, C.byref(state), 8,
                                    C.byref(length), chars) == 0 and length.value == 1:
                    upper = chr(chars[0]).upper()
                    if len(upper) == 1:
                        result.setdefault(ord(upper), native)
        finally:
            cf.CFRelease(source)
        return result

    def register(self, name, value):
        key, modifiers = combination(value)
        functions = [122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111, 105, 107, 113, 106, 64, 79, 80, 90]
        special = {int(Qt.Key.Key_Left): 123, int(Qt.Key.Key_Right): 124,
                   int(Qt.Key.Key_Down): 125, int(Qt.Key.Key_Up): 126,
                   int(Qt.Key.Key_PageUp): 116, int(Qt.Key.Key_PageDown): 121,
                   int(Qt.Key.Key_Home): 115, int(Qt.Key.Key_End): 119,
                   int(Qt.Key.Key_Space): 49, int(Qt.Key.Key_Return): 36,
                   int(Qt.Key.Key_Enter): 76, int(Qt.Key.Key_Escape): 53}
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F20:
            native = functions[key - int(Qt.Key.Key_F1)]
        elif key in special:
            native = special[key]
        else:
            if self.layout_keys is None:
                self.layout_keys = self.character_keys()
            native = self.layout_keys.get(key)
        if native is None:
            raise ValueError(tr('Nieobsługiwany skrót globalny.'))
        identifier = next(_IDS)
        reference = C.c_void_p()
        # Qt Control is Command on macOS; Qt Meta represents the physical Control key.
        flags = native_modifiers(modifiers, 1 << 8, 1 << 11, 1 << 9, 1 << 12)
        result = self.carbon.RegisterEventHotKey(native, flags, self.HotKeyID(0x4D544D52, identifier),
                                                self.carbon.GetApplicationEventTarget(), 0, C.byref(reference))
        if result != 0:
            raise ValueError(tr('Skrót zajęty lub zablokowany przez system.'))
        self.handles[identifier] = (name, reference)

    def handle_event(self, _next, event, _data):
        identifier = self.HotKeyID()
        status = self.carbon.GetEventParameter(event, 0x2D2D2D2D, 0x686B6964, None,
                                               C.sizeof(identifier), None, C.byref(identifier))
        if status == 0 and identifier.signature == 0x4D544D52 and identifier.id in self.handles:
            if self.carbon.GetEventKind(event) == 6:
                self.pressed.discard(identifier.id)
            elif identifier.id not in self.pressed:
                self.pressed.add(identifier.id)
                self.callback(self.handles[identifier.id][0])
            return 0
        return -9874  # eventNotHandledErr: let unrelated Carbon handlers process the event.

    def clear(self):
        for _name, reference in self.handles.values():
            self.carbon.UnregisterEventHotKey(reference)
        self.handles.clear()
        self.pressed.clear()

    def close(self):
        self.clear()
        self.carbon.RemoveEventHandler(self.handler_ref)


class X11Backend:
    class KeyEvent(C.Structure):
        _fields_ = [('type', C.c_int), ('serial', C.c_ulong), ('send_event', C.c_int),
                    ('display', C.c_void_p), ('window', C.c_ulong), ('root', C.c_ulong),
                    ('subwindow', C.c_ulong), ('time', C.c_ulong), ('x', C.c_int),
                    ('y', C.c_int), ('x_root', C.c_int), ('y_root', C.c_int),
                    ('state', C.c_uint), ('keycode', C.c_uint), ('same_screen', C.c_int)]

    class Event(C.Union):
        _fields_ = [('type', C.c_int), ('pad', C.c_long * 24)]

    class Error(C.Structure):
        _fields_ = [('type', C.c_int), ('display', C.c_void_p), ('resourceid', C.c_ulong),
                    ('serial', C.c_ulong), ('error_code', C.c_ubyte),
                    ('request_code', C.c_ubyte), ('minor_code', C.c_ubyte)]

    class ModifierMap(C.Structure):
        _fields_ = [('max_keypermod', C.c_int), ('modifiermap', C.POINTER(C.c_ubyte))]

    def __init__(self, callback):
        self.callback = callback
        self.bindings = {}
        self.grabs = []
        self.pressed = set()
        self.x = C.CDLL(find_library('X11') or 'libX11.so.6')
        x = self.x
        definitions = {
            'XOpenDisplay': ([C.c_char_p], C.c_void_p),
            'XCloseDisplay': ([C.c_void_p], C.c_int),
            'XDefaultRootWindow': ([C.c_void_p], C.c_ulong),
            'XConnectionNumber': ([C.c_void_p], C.c_int),
            'XStringToKeysym': ([C.c_char_p], C.c_ulong),
            'XKeysymToKeycode': ([C.c_void_p, C.c_ulong], C.c_ubyte),
            'XGrabKey': ([C.c_void_p, C.c_int, C.c_uint, C.c_ulong, C.c_int, C.c_int, C.c_int], C.c_int),
            'XUngrabKey': ([C.c_void_p, C.c_int, C.c_uint, C.c_ulong], C.c_int),
            'XSync': ([C.c_void_p, C.c_int], C.c_int),
            'XPending': ([C.c_void_p], C.c_int),
            'XNextEvent': ([C.c_void_p, C.POINTER(self.Event)], C.c_int),
            'XPeekEvent': ([C.c_void_p, C.POINTER(self.Event)], C.c_int),
            'XGetModifierMapping': ([C.c_void_p], C.POINTER(self.ModifierMap)),
            'XFreeModifiermap': ([C.POINTER(self.ModifierMap)], C.c_int),
            'XkbSetDetectableAutoRepeat': ([C.c_void_p, C.c_int, C.POINTER(C.c_int)], C.c_int),
        }
        for name, (arguments, returns) in definitions.items():
            function = getattr(x, name)
            function.argtypes, function.restype = arguments, returns
        self.display = x.XOpenDisplay(None)
        if not self.display:
            raise OSError(tr('Brak dostępu do sesji X11.'))
        self.root = x.XDefaultRootWindow(self.display)
        supported = C.c_int()
        x.XkbSetDetectableAutoRepeat(self.display, 1, C.byref(supported))
        self.locks = {0}
        mapping = x.XGetModifierMapping(self.display)
        if mapping:
            try:
                lock_keys = {x.XKeysymToKeycode(self.display, symbol) for symbol in (0xFFE5, 0xFF7F, 0xFF14)} - {0}
                for index in range(8):
                    if any(mapping.contents.modifiermap[index * mapping.contents.max_keypermod + j] in lock_keys
                           for j in range(mapping.contents.max_keypermod)):
                        self.locks |= {mask | (1 << index) for mask in list(self.locks)}
            finally:
                x.XFreeModifiermap(mapping)
        self.error_type = C.CFUNCTYPE(C.c_int, C.c_void_p, C.POINTER(self.Error))
        x.XSetErrorHandler.argtypes = [C.c_void_p]
        x.XSetErrorHandler.restype = C.c_void_p
        self.notifier = QSocketNotifier(x.XConnectionNumber(self.display), QSocketNotifier.Type.Read)
        self.notifier.activated.connect(self.drain)

    def register(self, name, value):
        key, modifiers = combination(value)
        special = {int(Qt.Key.Key_Left): 'Left', int(Qt.Key.Key_Right): 'Right',
                   int(Qt.Key.Key_Up): 'Up', int(Qt.Key.Key_Down): 'Down',
                   int(Qt.Key.Key_PageUp): 'Prior', int(Qt.Key.Key_PageDown): 'Next',
                   int(Qt.Key.Key_Home): 'Home', int(Qt.Key.Key_End): 'End',
                   int(Qt.Key.Key_Space): 'space', int(Qt.Key.Key_Return): 'Return',
                   int(Qt.Key.Key_Enter): 'KP_Enter', int(Qt.Key.Key_Escape): 'Escape'}
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F35:
            symbol = self.x.XStringToKeysym(f'F{key - int(Qt.Key.Key_F1) + 1}'.encode())
        elif key in special:
            symbol = self.x.XStringToKeysym(special[key].encode())
        elif 0 < key < 0x10000:
            lower = chr(key).lower()
            symbol = ord(lower) if len(lower) == 1 else key
            if symbol > 255:
                symbol |= 0x01000000
        else:
            raise ValueError(tr('Nieobsługiwany skrót globalny.'))
        code = self.x.XKeysymToKeycode(self.display, symbol)
        mask = native_modifiers(modifiers, 4, 8, 1, 64)
        if not code:
            raise ValueError(tr('Nieobsługiwany skrót globalny.'))
        if (code, mask) in self.bindings:
            raise ValueError(tr('Skrót zajęty lub zablokowany przez system.'))
        failures = []
        old_handler = None

        def catch_error(display, event):
            if display == self.display and event.contents.request_code == 33:
                failures.append(event.contents.error_code)
                return 0
            if old_handler:
                return self.error_type(old_handler)(display, event)
            return 0

        handler = self.error_type(catch_error)
        self.x.XSync(self.display, 0)
        old_handler = self.x.XSetErrorHandler(C.cast(handler, C.c_void_p))
        try:
            for lock in self.locks:
                self.x.XGrabKey(self.display, code, mask | lock, self.root, 0, 1, 1)
            self.x.XSync(self.display, 0)
        finally:
            self.x.XSetErrorHandler(old_handler)
        if failures:
            for lock in self.locks:
                self.x.XUngrabKey(self.display, code, mask | lock, self.root)
            self.x.XSync(self.display, 0)
            raise ValueError(tr('Skrót zajęty lub zablokowany przez system.'))
        self.bindings[code, mask] = name
        self.grabs.append((code, mask))

    def drain(self, *_):
        while self.display and self.x.XPending(self.display):
            event = self.Event()
            self.x.XNextEvent(self.display, C.byref(event))
            if event.type not in (2, 3):
                continue
            key = C.cast(C.byref(event), C.POINTER(self.KeyEvent)).contents
            if event.type == 3:
                # X11 servers without detectable auto-repeat synthesize release/press pairs.
                if self.x.XPending(self.display):
                    following = self.Event()
                    self.x.XPeekEvent(self.display, C.byref(following))
                    next_key = C.cast(C.byref(following), C.POINTER(self.KeyEvent)).contents
                    if following.type == 2 and next_key.keycode == key.keycode and next_key.time == key.time:
                        continue
                self.pressed.discard(key.keycode)
            elif key.keycode not in self.pressed:
                self.pressed.add(key.keycode)
                name = self.bindings.get((key.keycode, key.state & (1 | 4 | 8 | 64)))
                if name:
                    self.callback(name)

    def clear(self):
        if not self.display:
            return
        for code, mask in self.grabs:
            for lock in self.locks:
                self.x.XUngrabKey(self.display, code, mask | lock, self.root)
        self.x.XSync(self.display, 0)
        self.bindings.clear()
        self.grabs.clear()
        self.pressed.clear()

    def close(self):
        self.clear()
        self.notifier.setEnabled(False)
        self.notifier.deleteLater()
        if self.display:
            self.x.XCloseDisplay(self.display)
            self.display = None


def create_backend(callback):
    app = QApplication.instance()
    if app.platformName() in ('offscreen', 'minimal'):
        raise OSError(tr('Skróty globalne niedostępne w trybie diagnostycznym.'))
    if sys.platform == 'win32':
        return WindowsBackend(callback)
    if sys.platform == 'darwin':
        return MacBackend(callback)
    if os.environ.get('XDG_SESSION_TYPE') == 'wayland' or 'wayland' in app.platformName():
        raise OSError(tr('Wayland: skróty globalne wymagają obsługi portalu pulpitu. Dostępne są skróty lokalne.'))
    return X11Backend(callback)


class GlobalHotkeys(QObject):
    activated = Signal(str)
    status_changed = Signal()

    def __init__(self, actions, parent=None, factory=create_backend, on_activate=None):
        super().__init__(parent)
        self.actions = actions
        self.factory = factory
        self.on_activate = on_activate
        self.backend = None
        self.errors = {}
        self.registered = set()
        self.activated.connect(self.dispatch, Qt.ConnectionType.QueuedConnection)
        QApplication.instance().aboutToQuit.connect(self.close)
        if parent:
            parent.destroyed.connect(self.close)

    def configure(self, values, enabled=True):
        if self.backend:
            self.backend.clear()
        self.errors.clear()
        self.registered.clear()
        if enabled:
            try:
                if not self.backend:
                    self.backend = self.factory(self.activated.emit)
                for name in GLOBAL_DEFAULTS:
                    if value := values.get(name):
                        try:
                            self.backend.register(name, value)
                            self.registered.add(name)
                        except (OSError, ValueError) as error:
                            self.errors[name] = str(error)
            except (OSError, ValueError, AttributeError) as error:
                self.errors['backend'] = str(error)
        self.status_changed.emit()

    def dispatch(self, name):
        if name in self.registered and not QApplication.activeModalWidget():
            action = self.actions.get(name)
            if action and action.isEnabled():
                self.on_activate(name) if self.on_activate else action.trigger()

    def status(self):
        if self.errors:
            lines = []
            for name, error in self.errors.items():
                title = self.actions[name].text() if name in self.actions else tr('Skróty globalne')
                lines.append(f'{title}: {tr(error)}')
            return '\n'.join(lines)
        if self.registered:
            return tr('Skróty globalne aktywne: {count}', count=len(self.registered))
        return tr('Skróty globalne wyłączone.')

    def close(self):
        if self.backend:
            self.backend.close()
            self.backend = None
        self.registered.clear()
