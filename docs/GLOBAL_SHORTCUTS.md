# Skróty globalne / Global shortcuts

Domyślnie Ctrl+Alt+Shift + B / N / P / U / I / O oznacza poprzedni punkt /
następny punkt / start-pauza / +1 min / +5 min / własną liczbę minut.
Na macOS Qt Ctrl oznacza Command. Własny przyrost ustawisz w Pomoc → Skróty
klawiaturowe… (1–120 minut). Jest też przełącznik wyłączający globalne sterowanie.

Defaults: Ctrl+Alt+Shift + B / N / P / U / I / O = previous / next / start-pause /
+1 minute / +5 minutes / custom minutes. On macOS Ctrl means Command. Set custom
minutes (1–120) and enable/disable global controls in Help → Keyboard shortcuts….

Global controls work while another app has focus, including presentations and
when the timer is hidden. Other shortcuts, such as file operations, remain local.
Configuration dialogs suspend registrations so the editor can receive the keys.
Modal dialogs suspend activation; exiting releases the registrations. Occupied
or unsupported combinations produce an explicit status; they are not silently
presented as working globally. Window shortcuts remain usable if registration fails.

## Platformy / Platforms

- Windows: RegisterHotKey / UnregisterHotKey, WM_HOTKEY; MOD_NOREPEAT.
  F12 is reserved by Windows and is rejected for global registration.
- macOS: RegisterEventHotKey, Carbon event handler and the current keyboard layout.
  Press/release tracking prevents held-key repeats. No global keyboard event tap.
- Linux X11: XGrabKey, dedicated connection and Qt socket notifier. Caps/Num/Scroll
  Lock variants are accounted for; conflicts are checked synchronously. No polling.
- Wayland: this beta has no GlobalShortcuts portal backend. The UI reports this
  limitation. Xwayland does not provide a general solution for native Wayland apps.

## Weryfikacja / Verification

Synthetic X11 desktop test: the active window belonged to a separate xmessage
process. Previous/next, pause/resume, +1/+5 and custom +3 minutes worked without
changing focus. A second connection detected a real registration conflict; a new
connection could claim the key after cleanup. No audio, screenshot capture or
private meeting data were involved.

Windows/macOS tests use registered native APIs and synthetic messages/events;
they do not replace a physical-keyboard test with PowerPoint/Keynote on real devices.

## Primary references

- [Microsoft RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey)
- [Qt native event filters](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QAbstractNativeEventFilter.html)
- [X11 XGrabKey](https://www.x.org/releases/current/doc/man/man3/XGrabKey.3.xhtml)
- [GlobalShortcuts portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html)

Repeat the X11 integration test from sources with an isolated synthetic meeting:
`QT_QPA_PLATFORM=xcb .venv/bin/python scripts/verify_global_shortcuts_x11.py`.
Requires an X11 desktop, xdotool and xmessage; none is an application dependency.
