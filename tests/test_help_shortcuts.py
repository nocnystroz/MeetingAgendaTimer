import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QKeySequence, QTextDocument
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from meeting_timer.documents import HelpDialog, documentation_root
from meeting_timer.i18n import set_language
from meeting_timer.model import Item
from meeting_timer.shortcuts import ShortcutsDialog, validate
from meeting_timer.windows import MainWindow


@pytest.fixture
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    set_language("pl", app)
    monkeypatch.setenv("MEETING_TIMER_DATA_DIR", str(tmp_path))
    widget = MainWindow()
    widget.tick_timer.stop()
    yield widget
    widget.save_timer.stop()
    widget.tray.hide()
    widget.counter.hide()
    widget.hide()
    widget.deleteLater()
    app.processEvents()
    set_language("pl", app)


@pytest.mark.parametrize("code,last", [
    ("pl", "7. Skróty i pomoc"), ("en", "7. Shortcuts and help"),
    ("de", "7. Tastenkürzel und Hilfe"), ("fr", "7. Raccourcis et aide"),
])
def test_help_renders_all_chapters_and_local_images(window, code, last):
    set_language(code)
    dialog = HelpDialog(window)
    try:
        assert dialog.contents.count() == 7
        assert last in dialog.browser.toPlainText()
        assert len(dialog.browser.toPlainText()) > 3000
        block = dialog.browser.document().begin()
        images = []
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                if fragment.charFormat().isImageFormat():
                    fmt = fragment.charFormat().toImageFormat()
                    image = dialog.browser.document().resource(QTextDocument.ResourceType.ImageResource, QUrl(fmt.name()))
                    assert image is not None and not image.isNull()
                    assert fmt.width() <= 680
                    images.append(fmt.name())
                iterator += 1
            block = block.next()
        assert len(images) == 2
        assert dialog.browser.loadResource(QTextDocument.ResourceType.ImageResource, QUrl("https://invalid.test/image.png")) is None
        assert dialog.browser.loadResource(QTextDocument.ResourceType.ImageResource, QUrl.fromLocalFile(str(documentation_root() / "PRIVACY.md"))) is None
    finally:
        dialog.close()


def test_shortcut_changes_are_atomic_and_persist_without_meeting(window):
    before = window.shortcuts.values()
    conflict = dict(before, play="Ctrl+L")
    with pytest.raises(ValueError, match="Konflikt"):
        window.shortcuts.apply(conflict, save=True)
    assert window.shortcuts.values() == before
    assert not window.shortcuts.path.exists()
    values = dict(before, play="Ctrl+Shift+P", counter="")
    window.shortcuts.apply(values, save=True)
    assert window.shortcuts.path.is_file()
    window.shortcuts.apply(window.shortcuts.defaults)
    assert window.shortcuts.load()
    assert window.shortcuts.values() == values
    dialog = ShortcutsDialog(window.shortcuts, window)
    dialog.restore_defaults()
    assert dialog.editors["play"].keySequence() == QKeySequence(window.shortcuts.defaults["play"])
    dialog.reject()
    assert window.shortcuts.values() == values


def test_shortcut_does_not_steal_plain_typing(window):
    with pytest.raises(ValueError):
        validate({"Play": "P"})
    with pytest.raises(ValueError):
        validate({"Play": "Ctrl+P, Ctrl+N"})
    validate({"Play": "F8", "Off": ""})


def test_custom_shortcut_triggers_in_both_windows(window):
    window.replace_items([Item("A", 120)])
    window.shortcuts.apply({"play": "Ctrl+Shift+P"})
    for target in [window, window.counter]:
        target.show()
        target.activateWindow()
        target.setFocus()
        QApplication.processEvents()
        was_started, was_paused = window.engine.started, window.engine.paused
        QTest.keyClick(target, Qt.Key.Key_P,
                       Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        QApplication.processEvents()
        assert window.engine.started
        assert not was_started or window.engine.paused != was_paused


def test_help_menu_has_one_privacy_item_and_explicit_links(window, monkeypatch):
    titles = [action.text() for action in window.help_menu.actions()]
    assert "Obsługa i prywatność" not in titles
    assert sum("prywatności" in text for text in titles) == 1
    opened = []
    monkeypatch.setattr(window, "open_link", opened.append)
    window.open_feedback()
    window.open_project()
    assert opened[0].endswith("/issues/new/choose")
    assert opened[1].startswith("https://ion301.com/")


class FakeGlobalBackend:
    def __init__(self, callback):
        self.callback = callback
        self.keys = {}
        self.closed = False
        self.reject = set()

    def register(self, name, value):
        if name in self.reject:
            raise ValueError('Skrót zajęty lub zablokowany przez system.')
        self.keys[name] = value

    def clear(self):
        self.keys.clear()

    def close(self):
        self.clear()
        self.closed = True


def fake_globals(window):
    manager = window.shortcuts.global_hotkeys
    manager.close()
    manager.factory = FakeGlobalBackend
    manager.configure(window.shortcuts.values(), True)
    return manager


def test_global_dispatch_changes_agenda_without_revealing_windows(window):
    manager = fake_globals(window)
    window.replace_items([Item('A', 120), Item('B', 180)])
    window.hide()
    window.counter.hide()
    manager.activated.emit('play')
    QApplication.processEvents()
    assert window.engine.started
    assert not window.isVisible() and not window.counter.isVisible()
    manager.activated.emit('next')
    QApplication.processEvents()
    assert window.engine.snapshot().index == 1
    assert not window.counter.isVisible()
    window.shortcuts.extra_minutes = 3
    before = window.meeting.items[1].seconds
    manager.activated.emit('add_custom')
    QApplication.processEvents()
    assert window.meeting.items[1].seconds == before + 180
    manager.configure(window.shortcuts.values(), False)
    manager.activated.emit('previous')
    QApplication.processEvents()
    assert window.engine.snapshot().index == 1
    assert not manager.backend.keys


def test_global_native_conflict_is_visible_and_does_not_hide_successes(window):
    manager = fake_globals(window)
    manager.backend.reject.add('next')
    manager.configure(window.shortcuts.values(), True)
    assert 'next' not in manager.registered
    assert 'previous' in manager.registered
    assert 'next' in manager.errors
    assert 'konfiguracji' in window.hotkey_summary.text()
    assert 'Następny punkt' in window.hotkey_summary.toolTip()
    backend = manager.backend
    manager.close()
    assert backend.closed and not backend.keys


def test_shortcut_editor_releases_system_grabs_until_closed(window):
    manager = fake_globals(window)
    assert manager.backend.keys
    dialog = ShortcutsDialog(window.shortcuts, window)
    assert not manager.backend.keys
    dialog.reject()
    assert manager.backend.keys


def test_legacy_window_bindings_migrate_to_unusual_global_defaults(window):
    from meeting_timer.global_hotkeys import GLOBAL_DEFAULTS
    from meeting_timer.storage import atomic_json
    atomic_json(window.shortcuts.path, {'play':'Ctrl+Return', 'save':'Ctrl+Shift+S'})
    assert window.shortcuts.load()
    assert window.shortcuts.values()['play'] == GLOBAL_DEFAULTS['play']
    assert window.shortcuts.values()['save'] == 'Ctrl+Shift+S'
    window.shortcuts.apply(window.shortcuts.values(), save=True, global_enabled=False, extra_minutes=7)
    window.shortcuts.extra_minutes = 5
    window.shortcuts.global_enabled = True
    assert window.shortcuts.load()
    assert window.shortcuts.extra_minutes == 7
    assert not window.shortcuts.global_enabled


def test_global_dispatch_is_suspended_in_modal_dialogs(window):
    from PySide6.QtWidgets import QDialog
    manager = fake_globals(window)
    window.replace_items([Item('A', 120), Item('B', 180)])
    dialog = QDialog(window)
    dialog.setModal(True)
    dialog.show()
    QApplication.processEvents()
    manager.activated.emit('next')
    QApplication.processEvents()
    assert window.engine.snapshot().index == 0
    dialog.close()
