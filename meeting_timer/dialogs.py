from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .engine import format_time
from .parser import ParseError, parse_agenda

EXAMPLE = "Wprowadzenie — 5 min\nOmówienie wyników — 15 min\nDecyzje i następne kroki — 10 min"


class AgendaDialog(QDialog):
    def __init__(self, parent=None, text="", replacing=False):
        super().__init__(parent)
        self.setWindowTitle("Wklej agendę")
        self.resize(650, 600)
        self.items = []
        layout = QVBoxLayout(self)
        tip = QLabel("Wklej tekst, tabelę z Excela/Sheets, CSV lub Markdown. Przykłady: Tytuł — 15 minut; 10:00–10:15 Tytuł; Tytuł (00:15:00). Godziny rozpoczęcia wymagają końcowego czasu lub wiersza HH:MM Koniec.")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        if replacing:
            note = QLabel("Nowy plan zastąpi bieżącą agendę. Stare punkty i ich notatki zostaną zachowane w danych tej sesji. Licznik zostanie zatrzymany; nagranie trwa niezależnie.")
            note.setWordWrap(True)
            note.setObjectName("warning")
            layout.addWidget(note)
        self.text = QPlainTextEdit(text or EXAMPLE)
        self.text.setMinimumHeight(150)
        layout.addWidget(self.text)
        self.preview = QTableWidget(0, 2)
        self.preview.setHorizontalHeaderLabels(["Rozpoznany punkt", "Czas"])
        self.preview.horizontalHeader().setStretchLastSection(True)
        self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.preview)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setObjectName("warning")
        self.error.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.error)
        row = QHBoxLayout()
        check = QPushButton("Sprawdź podgląd")
        check.clicked.connect(self.validate)
        row.addWidget(check)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Zastosuj agendę")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        row.addWidget(self.buttons)
        layout.addLayout(row)
        self.text.textChanged.connect(self.invalidate)
        self.validate()

    def invalidate(self):
        self.items = []
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.error.setText("Tekst zmieniony — sprawdź podgląd przed zastosowaniem.")

    def validate(self):
        try:
            self.items = parse_agenda(self.text.toPlainText())
        except ParseError as exc:
            self.preview.setRowCount(0)
            self.error.setText(str(exc))
            self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            return
        self.preview.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            self.preview.setItem(row, 0, QTableWidgetItem(item.title))
            self.preview.setItem(row, 1, QTableWidgetItem(format_time(item.seconds)))
        self.preview.setColumnWidth(0, 420)
        self.error.setText(f"{len(self.items)} punktów · łącznie {format_time(sum(i.seconds for i in self.items))}")
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zakres eksportu")
        layout = QVBoxLayout(self)
        self.checks = {}
        for key, label, checked in [("notes", "Notatki", True), ("decisions", "Decyzje", True),
                                    ("tasks", "Zadania", True), ("transcripts", "Transkrypcje", False)]:
            check = QCheckBox(label)
            check.setChecked(checked)
            self.checks[key] = check
            layout.addWidget(check)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def options(self):
        return {key: check.isChecked() for key, check in self.checks.items()}
