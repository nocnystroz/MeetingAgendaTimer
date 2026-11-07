"""Local help documents and explicit first-run acceptance."""

import hashlib
import time
from pathlib import Path

from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QTextBrowser, QVBoxLayout

from .i18n import LANGUAGES, Button, language, set_language
from .storage import atomic_json, read_json
from .widgets import ComboBox

ASSETS = Path(__file__).parent / "assets"
SUPPORT_URL = "https://buymeacoffee.com/m.slawinski"


def terms_text(code=None):
    return (ASSETS / f"terms.{code or language()}.md").read_text(encoding="utf-8")


def terms_version():
    return hashlib.sha256(b"".join((ASSETS / f"terms.{code}.md").read_bytes()
                                   for code in LANGUAGES)).hexdigest()


def document_text(name):
    return (Path(__file__).resolve().parents[1] / name).read_text(encoding="utf-8")


class DocumentDialog(QDialog):
    def __init__(self, title, text, parent=None, plain=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(780, 620)
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setPlainText(text) if plain else self.browser.setMarkdown(text)
        layout.addWidget(self.browser)
        close = Button("Zamknij")
        close.clicked.connect(self.accept)
        layout.addWidget(close)


class TermsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Warunki użytkowania")
        self.resize(800, 650)
        layout = QVBoxLayout(self)
        self.languages = ComboBox()
        for code, native in LANGUAGES.items():
            self.languages.addItem(native, code)
        self.languages.setCurrentIndex(list(LANGUAGES).index(language()))
        self.languages.currentIndexChanged.connect(self.change_language)
        layout.addWidget(self.languages)
        self.browser = QTextBrowser()
        self.browser.setMarkdown(terms_text())
        layout.addWidget(self.browser, 1)
        self.consent = QCheckBox("Akceptuję warunki i potwierdzam wymagane zgody uczestników.")
        layout.addWidget(self.consent)
        row = QHBoxLayout()
        self.cancel = Button("Nie akceptuję — zakończ")
        self.cancel.clicked.connect(self.reject)
        self.agree = Button("Akceptuję i uruchamiam")
        self.agree.setObjectName("primary")
        self.agree.setEnabled(False)
        self.agree.clicked.connect(self.accept)
        self.consent.toggled.connect(self.agree.setEnabled)
        row.addWidget(self.cancel)
        row.addWidget(self.agree)
        layout.addLayout(row)

    def change_language(self, _index):
        set_language(self.languages.currentData())
        self.browser.setMarkdown(terms_text())


def ensure_accepted(directory, parent=None):
    path = Path(directory) / "consent.json"
    try:
        data = read_json(path)
        if data.get("terms_version") == terms_version() and data.get("accepted") is True:
            set_language(data.get("language", "pl"))
            return True
    except (OSError, ValueError, AttributeError):
        pass
    dialog = TermsDialog(parent)
    if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.consent.isChecked():
        return False
    atomic_json(path, {"accepted": True, "terms_version": terms_version(),
                      "accepted_at": time.time(), "language": language()})
    return True
