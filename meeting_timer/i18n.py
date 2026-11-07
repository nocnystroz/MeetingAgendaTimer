"""Small local catalog and live widget retranslation. User documents are never translated."""

import json
import re
import string
import weakref
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QEvent, QLibraryInfo, QLocale, QObject, Qt, QTranslator
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTabWidget,
    QTextEdit,
)
from shiboken6 import isValid

LANGUAGES = {"pl": "Polski", "en": "English", "de": "Deutsch", "fr": "Français"}
_language = "pl"
_catalog = None
_patterns = None
_sources = weakref.WeakKeyDictionary()


def language():
    return _language


def catalog():
    global _catalog
    if _catalog is None:
        _catalog = json.loads((Path(__file__).parent / "assets/translations.json").read_text(encoding="utf-8"))
    return _catalog


def patterns():
    global _patterns
    if _patterns is None:
        _patterns = []
        formatter = string.Formatter()
        for source in catalog():
            if "{" not in source:
                continue
            regex, names, literal_size = "", [], 0
            for literal, name, _, _ in formatter.parse(source):
                regex += re.escape(literal)
                literal_size += len(literal)
                if name is not None:
                    names.append(name)
                    regex += "(.+?)"
            if literal_size >= 3:
                _patterns.append((literal_size, re.compile(regex, re.DOTALL), source, names))
        _patterns.sort(key=lambda entry: entry[0], reverse=True)
    return _patterns


@lru_cache(maxsize=4096)
def _translate(text, code):
    if code == "pl" or not text:
        return text
    if entry := catalog().get(text):
        return entry.get(code, text)
    for _, regex, source, names in patterns():
        match = regex.fullmatch(text)
        if match:
            values = dict(zip(names, match.groups()))
            for key in ("error", "state", "status"):
                if key in values and values[key] != text:
                    values[key] = _translate(values[key], code)
            return catalog()[source][code].format(**values)
    if "\n" in text:
        return "\n".join(_translate(line, code) for line in text.split("\n"))
    return text


def tr(text, **values):
    result = _translate(str(text), _language)
    return result.format(**values) if values else result


class Label(QLabel):
    def __init__(self, text="", parent=None, translate=True):
        super().__init__(parent)
        self.translate_enabled = translate
        self.source_text = str(text)
        self.retranslate()

    def setText(self, text):
        self.source_text = str(text)
        self.retranslate()

    def retranslate(self):
        super().setText(tr(self.source_text) if self.translate_enabled else self.source_text)


class Button(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.source_text = str(text)
        self.retranslate()

    def setText(self, text):
        self.source_text = str(text)
        self.retranslate()

    def retranslate(self):
        super().setText(tr(self.source_text))


class StatusBar(QStatusBar):
    def showMessage(self, text, timeout=0):
        self.source_text, self.source_timeout = str(text), timeout
        super().showMessage(tr(text), timeout)

    def retranslate(self):
        super().showMessage(tr(getattr(self, "source_text", "")), getattr(self, "source_timeout", 0))


def _property(obj, key, getter, setter):
    values = _sources.setdefault(obj, {})
    current = getter()
    previous = values.get(key)
    source = previous[0] if previous and current == previous[1] else current
    translated = tr(source)
    values[key] = (source, translated)
    if current != translated:
        setter(translated)


def localize(obj):
    if not isValid(obj):
        return
    if isinstance(obj, (Label, Button, StatusBar)):
        obj.retranslate()
    elif isinstance(obj, (QLabel, QPushButton, QCheckBox, QAction)):
        _property(obj, "text", obj.text, obj.setText)
    if hasattr(obj, "windowTitle"):
        _property(obj, "windowTitle", obj.windowTitle, obj.setWindowTitle)
        _property(obj, "tooltip", obj.toolTip, obj.setToolTip)
    if isinstance(obj, (QLineEdit, QPlainTextEdit, QTextEdit)):
        _property(obj, "placeholder", obj.placeholderText, obj.setPlaceholderText)
    if isinstance(obj, QGroupBox):
        _property(obj, "title", obj.title, obj.setTitle)
    if isinstance(obj, QProgressBar):
        _property(obj, "format", obj.format, obj.setFormat)
    if isinstance(obj, QInputDialog):
        _property(obj, "prompt", obj.labelText, obj.setLabelText)
    if isinstance(obj, QMessageBox):
        obj.setTextFormat(Qt.TextFormat.PlainText)
        _property(obj, "body", obj.text, obj.setText)
        _property(obj, "info", obj.informativeText, obj.setInformativeText)
    if isinstance(obj, QTabWidget):
        for index in range(obj.count()):
            _property(obj, f"tab{index}", lambda i=index: obj.tabText(i), lambda text, i=index: obj.setTabText(i, text))
    if isinstance(obj, QTableWidget):
        for column in range(obj.columnCount()):
            if header := obj.horizontalHeaderItem(column):
                _property(obj, f"header{column}", header.text, header.setText)
    if hasattr(obj, "retranslate_items"):
        obj.retranslate_items()


class Filter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            localize(obj)
            for action in obj.findChildren(QAction):
                localize(action)
        return False


def install(app):
    if not hasattr(app, "i18n_filter"):
        app.i18n_filter = Filter(app)
        app.installEventFilter(app.i18n_filter)


def set_language(code, app=None):
    global _language
    code = code if code in LANGUAGES else "pl"
    _language = code
    app = app or QApplication.instance()
    QLocale.setDefault(QLocale(code))
    if app is None:
        return
    install(app)
    if old := getattr(app, "qt_translator", None):
        app.removeTranslator(old)
    translator = QTranslator(app)
    if translator.load(f"qtbase_{code}", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)
    app.qt_translator = translator
    for widget in app.allWidgets():
        localize(widget)
        widget.setLocale(QLocale(code))
        for action in widget.findChildren(QAction):
            localize(action)
