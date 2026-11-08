"""Editable window shortcuts, stored separately from meeting content."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QKeySequenceEdit,
    QMessageBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .global_hotkeys import GLOBAL_DEFAULTS
from .i18n import Button, Label, tr
from .storage import atomic_json, read_json

PORTABLE = QKeySequence.SequenceFormat.PortableText


def normalize(value):
    return QKeySequence(value, PORTABLE).toString(PORTABLE)


def validate(bindings):
    """Reject ambiguous prefixes and bare typing keys before changing active bindings."""
    assigned = []
    for name, value in bindings.items():
        if not value:
            continue
        sequence = QKeySequence(value, PORTABLE)
        if (sequence.isEmpty() or sequence.count() != 1 or not sequence[0].key()
                or sequence[0].key() == Qt.Key.Key_unknown):
            raise ValueError(tr("Nieprawidłowy skrót: {name}", name=name))
        key = sequence[0]
        function_key = Qt.Key.Key_F1 <= key.key() <= Qt.Key.Key_F35
        modifiers = key.keyboardModifiers() & (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier)
        if not modifiers and not function_key:
            raise ValueError(tr("Skrót wymaga Ctrl, Alt, Cmd lub klawisza funkcyjnego: {name}", name=name))
        for previous_name, previous in assigned:
            if (sequence.matches(previous) != QKeySequence.SequenceMatch.NoMatch
                    or previous.matches(sequence) != QKeySequence.SequenceMatch.NoMatch):
                raise ValueError(tr("Konflikt skrótów: {first} / {second}", first=previous_name, second=name))
        assigned.append((name, sequence))


class ShortcutSettings:
    def __init__(self, path):
        self.path = path
        self.actions = {}
        self.defaults = {}
        self.global_enabled = True
        self.extra_minutes = 5
        self.global_hotkeys = None

    def register(self, name, action, default=""):
        self.actions[name] = action
        self.defaults[name] = normalize(default)
        action.setShortcut(QKeySequence(default))
        action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        action.setAutoRepeat(False)

    def values(self):
        return {name: action.shortcut().toString(PORTABLE) for name, action in self.actions.items()}

    def apply(self, values, save=False, global_enabled=None, extra_minutes=None):
        for name, value in values.items():
            if name in self.defaults and (not isinstance(value, str) or (value and not normalize(value))):
                raise ValueError(tr("Nieprawidłowy skrót: {name}", name=name))
        merged = {name: normalize(values.get(name, default)) for name, default in self.defaults.items()}
        validate({self.actions[name].text(): value for name, value in merged.items()})
        enabled = self.global_enabled if global_enabled is None else bool(global_enabled)
        minutes = self.extra_minutes if extra_minutes is None else int(extra_minutes)
        if not 1 <= minutes <= 120:
            raise ValueError(tr("Liczba minut musi być od 1 do 120."))
        if save:
            atomic_json(self.path, {"version": 2, "bindings": merged,
                                    "global_enabled": enabled, "extra_minutes": minutes})
        self.global_enabled, self.extra_minutes = enabled, minutes
        for name, value in merged.items():
            self.actions[name].setShortcut(QKeySequence(value, PORTABLE))
        if self.global_hotkeys:
            self.global_hotkeys.configure(merged, enabled)

    def load(self):
        try:
            saved = read_json(self.path)
            if not isinstance(saved, dict):
                return False
            if saved.get("version") == 2:
                bindings = saved["bindings"]
                enabled = saved.get("global_enabled", True)
                minutes = saved.get("extra_minutes", 5)
            else:
                # Earlier releases stored window-only shortcuts. Preserve their local use;
                # migrate meeting controls to the unusual global defaults once.
                bindings = dict(saved)
                bindings.update({key: value for key, value in GLOBAL_DEFAULTS.items() if key in self.defaults})
                enabled, minutes = True, 5
            if not isinstance(bindings, dict) or not all(isinstance(value, str) for value in bindings.values()):
                return False
            self.apply(bindings, global_enabled=enabled, extra_minutes=minutes)
        except FileNotFoundError:
            return True
        except (OSError, ValueError, TypeError, KeyError):
            return False
        return True


class ShortcutsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Skróty klawiaturowe")
        self.resize(730, 620)
        layout = QVBoxLayout(self)
        hint = Label("Skróty sterowania spotkaniem mogą działać także w prezentacji. Kliknij pole i naciśnij kombinację; wyczyść, aby wyłączyć.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.global_option = QCheckBox("Globalne sterowanie spotkaniem (także poza oknem aplikacji)")
        self.global_option.setChecked(settings.global_enabled)
        layout.addWidget(self.global_option)
        custom = QHBoxLayout()
        custom.addWidget(Label("Liczba minut dla skrótu własnego:"))
        self.extra_minutes = QSpinBox()
        self.extra_minutes.setRange(1, 120)
        self.extra_minutes.setValue(settings.extra_minutes)
        custom.addWidget(self.extra_minutes)
        custom.addStretch()
        layout.addLayout(custom)
        self.table = QTableWidget(len(settings.actions), 2)
        self.table.setHorizontalHeaderLabels(["Czynność", "Skrót"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 230)
        self.editors = {}
        for row, (name, action) in enumerate(settings.actions.items()):
            title = action.text().replace("&", "")
            if name in GLOBAL_DEFAULTS:
                title += " · " + tr("globalny")
            item = QTableWidgetItem(title)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item)
            editor = QKeySequenceEdit(action.shortcut())
            editor.setMaximumSequenceLength(1)
            editor.setClearButtonEnabled(True)
            self.editors[name] = editor
            self.table.setCellWidget(row, 1, editor)
            self.table.setRowHeight(row, 38)
        layout.addWidget(self.table)
        self.status = Label(settings.global_hotkeys.status() if settings.global_hotkeys else "")
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        defaults = Button("Przywróć domyślne")
        defaults.clicked.connect(self.restore_defaults)
        row.addWidget(defaults)
        row.addStretch()
        cancel = Button("Anuluj")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        save = Button("Zapisz")
        save.setObjectName("primary")
        save.clicked.connect(self.save)
        row.addWidget(save)
        layout.addLayout(row)
        if settings.global_hotkeys:
            # Unregister while editing so the key editor can receive registered chords.
            settings.global_hotkeys.configure({}, False)
            self.finished.connect(lambda _result: settings.global_hotkeys.configure(
                settings.values(), settings.global_enabled))

    def restore_defaults(self):
        self.global_option.setChecked(True)
        self.extra_minutes.setValue(5)
        for name, editor in self.editors.items():
            editor.setKeySequence(QKeySequence(self.settings.defaults[name], PORTABLE))

    def save(self):
        values = {name: editor.keySequence().toString(PORTABLE) for name, editor in self.editors.items()}
        try:
            self.settings.apply(values, save=True, global_enabled=self.global_option.isChecked(),
                                extra_minutes=self.extra_minutes.value())
        except ValueError as error:
            QMessageBox.warning(self, tr("Skróty klawiaturowe"), str(error))
            return
        except OSError:
            QMessageBox.warning(self, tr("Nie można zapisać"), tr("Nie można zapisać skrótów klawiaturowych."))
            return
        manager = self.settings.global_hotkeys
        if self.global_option.isChecked() and manager and manager.errors:
            self.status.setText(manager.status())
            QMessageBox.warning(self, tr("Skróty globalne"), manager.status())
            manager.configure({}, False)
            return
        self.accept()
