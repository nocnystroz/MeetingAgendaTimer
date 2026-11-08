"""Local help documents and explicit first-run acceptance."""

import hashlib
import re
import sys
import time
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QListWidget,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
)

from .i18n import LANGUAGES, Button, language, set_language
from .storage import atomic_json, read_json
from .widgets import ComboBox

ASSETS = Path(__file__).parent / "assets"
SUPPORT_URL = "https://buymeacoffee.com/m.slawinski"
REPOSITORY_URL = "https://github.com/nocnystroz/MeetingAgendaTimer"
FEEDBACK_URL = REPOSITORY_URL + "/issues/new/choose"
PROJECT_URL = "https://ion301.com/pl/narzedzia/meeting-agenda-timer/"
PROJECT_URL_EN = "https://ion301.com/en/tools/meeting-agenda-timer/"


def terms_text(code=None):
    return (ASSETS / f"terms.{code or language()}.md").read_text(encoding="utf-8")


def terms_version():
    return hashlib.sha256(b"".join((ASSETS / f"terms.{code}.md").read_bytes()
                                   for code in LANGUAGES)).hexdigest()


def document_text(name):
    return (documentation_root() / name).read_text(encoding="utf-8")


def documentation_root():
    roots = [Path(__file__).resolve().parents[1], Path(sys.executable).parent,
             Path(sys.executable).parent.parent / "Resources"]
    return next((root for root in roots if (root / "docs/help").is_dir()), roots[0])


class LocalDocumentBrowser(QTextBrowser):
    """Help images are bundled; never load remote images or arbitrary local files."""

    def loadResource(self, resource_type, url):
        if resource_type == QTextDocument.ResourceType.ImageResource:
            resolved = self.document().baseUrl().resolved(url)
            path = Path(resolved.toLocalFile()).resolve()
            root = documentation_root().resolve()
            if not resolved.isLocalFile() or not path.is_relative_to(root / "docs/screenshots"):
                return None
        return super().loadResource(resource_type, url)


class DocumentDialog(QDialog):
    def __init__(self, title, text, parent=None, plain=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(780, 620)
        layout = QVBoxLayout(self)
        self.browser = LocalDocumentBrowser()
        self.browser.document().setBaseUrl(QUrl.fromLocalFile(str(documentation_root()) + "/"))
        self.browser.setOpenExternalLinks(True)
        self.browser.setPlainText(text) if plain else self.browser.setMarkdown(text)
        layout.addWidget(self.browser)
        close = Button("Zamknij")
        close.clicked.connect(self.accept)
        layout.addWidget(close)


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Instrukcja obsługi")
        self.resize(1040, 740)
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        self.contents = QListWidget()
        self.contents.setMaximumWidth(280)
        self.contents.setWordWrap(True)
        self.browser = LocalDocumentBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.document().setDocumentMargin(22)
        self.browser.document().setDefaultStyleSheet(
            "h1 { font-size: 26px; } h2 { font-size: 20px; margin-top: 26px; } "
            "p, li { line-height: 140%; } a { color: #168f83; }")
        root = documentation_root() / "docs/help"
        self.browser.document().setBaseUrl(QUrl.fromLocalFile(str(root) + "/"))
        text = (root / f"{language()}.md").read_text(encoding="utf-8")
        self.sections = re.findall(r"^## (.+)$", text, re.MULTILINE)
        self.contents.addItems(self.sections)
        count = iter(range(len(self.sections)))
        text = re.sub(r"^## (.+)$", lambda match: f'<a name="section-{next(count)}"></a>\n\n## {match[1]}',
                      text, flags=re.MULTILINE)
        self.browser.setMarkdown(text)
        block = self.browser.document().begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                if fragment.charFormat().isImageFormat():
                    image_format = fragment.charFormat().toImageFormat()
                    path = self.browser.document().baseUrl().resolved(QUrl(image_format.name()))
                    image = QImage(path.toLocalFile())
                    if not image.isNull():
                        width = min(680, image.width())
                        image_format.setWidth(width)
                        image_format.setHeight(image.height() * width / image.width())
                        cursor = QTextCursor(self.browser.document())
                        cursor.setPosition(fragment.position())
                        cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
                        cursor.setCharFormat(image_format)
                iterator += 1
            block = block.next()
        self.contents.currentRowChanged.connect(lambda row: self.browser.scrollToAnchor(f"section-{row}"))
        splitter.addWidget(self.contents)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)
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
