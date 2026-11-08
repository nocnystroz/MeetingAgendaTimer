"""Editable window shortcuts, stored separately from meeting content."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QKeySequenceEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

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

    def register(self, name, action, default=""):
        self.actions[name] = action
        self.defaults[name] = normalize(default)
        action.setShortcut(QKeySequence(default))
        action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        action.setAutoRepeat(False)

    def values(self):
        return {name: action.shortcut().toString(PORTABLE) for name, action in self.actions.items()}

    def apply(self, values, save=False):
        for name, value in values.items():
            if name in self.defaults and (not isinstance(value, str) or (value and not normalize(value))):
                raise ValueError(tr("Nieprawidłowy skrót: {name}", name=name))
        merged = {name: normalize(values.get(name, default)) for name, default in self.defaults.items()}
        validate({self.actions[name].text(): value for name, value in merged.items()})
        if save:
            atomic_json(self.path, merged)
        for name, value in merged.items():
            self.actions[name].setShortcut(QKeySequence(value, PORTABLE))

    def load(self):
        try:
            saved = read_json(self.path)
            if not isinstance(saved, dict) or not all(isinstance(value, str) for value in saved.values()):
                return False
            self.apply(saved)
        except FileNotFoundError:
            return True
        except (OSError, ValueError, TypeError):
            return False
        return True


class ShortcutsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Skróty klawiaturowe")
        self.resize(730, 620)
        layout = QVBoxLayout(self)
        hint = Label("Kliknij skrót i naciśnij kombinację. Wyczyść pole, aby go wyłączyć. Skróty działają w obu oknach aplikacji.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.table = QTableWidget(len(settings.actions), 2)
        self.table.setHorizontalHeaderLabels(["Czynność", "Skrót"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 230)
        self.editors = {}
        for row, (name, action) in enumerate(settings.actions.items()):
            item = QTableWidgetItem(action.text().replace("&", ""))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item)
            editor = QKeySequenceEdit(action.shortcut())
            editor.setMaximumSequenceLength(1)
            editor.setClearButtonEnabled(True)
            self.editors[name] = editor
            self.table.setCellWidget(row, 1, editor)
            self.table.setRowHeight(row, 38)
        layout.addWidget(self.table)
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

    def restore_defaults(self):
        for name, editor in self.editors.items():
            editor.setKeySequence(QKeySequence(self.settings.defaults[name], PORTABLE))

    def save(self):
        values = {name: editor.keySequence().toString(PORTABLE) for name, editor in self.editors.items()}
        try:
            self.settings.apply(values, save=True)
        except ValueError as error:
            QMessageBox.warning(self, tr("Skróty klawiaturowe"), str(error))
            return
        except OSError:
            QMessageBox.warning(self, tr("Nie można zapisać"), tr("Nie można zapisać skrótów klawiaturowych."))
            return
        self.accept()
