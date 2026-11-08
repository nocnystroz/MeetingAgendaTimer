"""Presenter and shared timer windows. No audio/network imported at startup."""

import math
import time
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, QDateTime, QSignalBlocker, Qt, QTimer
from PySide6.QtGui import QAction, QFontDatabase, QPdfWriter
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .dialogs import AgendaDialog, ExportDialog
from .engine import TimerEngine, format_time
from .exporting import markdown, pdf_document
from .i18n import LANGUAGES, Button, Label, StatusBar, install, language, set_language, tr
from .model import Item, Meeting, Task
from .storage import (
    atomic_json,
    data_directory,
    load_meeting,
    read_json,
    save_meeting,
    template_data,
)
from .theme import apply_theme, icon
from .version import build_info, version
from .widgets import ComboBox


def label(text="", name=None):
    widget = Label(text, translate=name not in ("counterTitle", "digits"))
    widget.setTextFormat(Qt.TextFormat.PlainText)
    if name:
        widget.setObjectName(name)
    return widget


def button(text, callback, image=None, primary=False):
    widget = Button(text)
    if image:
        widget.setIcon(icon(image))
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(callback)
    return widget


class CounterWindow(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("counter")
        self.setWindowTitle(f"Licznik · {version()}")
        self.setWindowIcon(icon("app"))
        self.resize(550, 370)
        self.setMinimumWidth(240)
        layout = QVBoxLayout(self)
        self.body_layout = layout
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)
        self.position = label("GOTOWY DO SPOTKANIA", "muted")
        self.title = label("Wklej agendę w panelu prowadzącego", "counterTitle")
        self.title.translate_enabled = True
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.full_title = self.title.text()
        self.time_color = "#26b7a4"
        self.digits = label("00:00", "digits")
        self.digits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.digits.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.next_label = label("", "muted")
        self.next_label.setWordWrap(True)
        self.state = label("", "muted")
        for widget in (self.position, self.title, self.digits, self.bar, self.state, self.next_label):
            layout.addWidget(widget)
        self.full_controls = QWidget()
        row = QHBoxLayout(self.full_controls)
        row.setContentsMargins(0, 0, 0, 0)
        self.pause = button("Start", owner.play_pause, "player-play", True)
        row.addWidget(self.pause)
        row.addWidget(button("+1 min", lambda: owner.add_time(60)))
        row.addWidget(button("Panel", owner.present))
        row.addWidget(button("Schowaj", lambda: owner.hide_to_tray(self)))
        layout.addWidget(self.full_controls)
        self.options = QWidget()
        options = QHBoxLayout(self.options)
        options.setContentsMargins(0, 0, 0, 0)
        self.pin = QCheckBox("Zawsze na wierzchu")
        self.pin.toggled.connect(self.set_pin)
        self.compact = QCheckBox("Kompaktowy")
        self.compact.toggled.connect(self.set_compact)
        options.addWidget(self.pin)
        options.addWidget(self.compact)
        layout.addWidget(self.options)
        self.mini_controls = QWidget()
        mini_row = QHBoxLayout(self.mini_controls)
        mini_row.setContentsMargins(0, 0, 0, 0)
        mini_row.setSpacing(4)
        self.mini_pause = button("", owner.play_pause, "player-play")
        self.mini_pin = QPushButton()
        self.mini_pin.setIcon(icon("pin"))
        self.mini_pin.setCheckable(True)
        self.mini_pin.setToolTip("Zawsze na wierzchu")
        self.mini_pin.setAccessibleName("Zawsze na wierzchu")
        self.mini_pin.toggled.connect(self.pin.setChecked)
        self.mini_panel = button("", owner.present, "notes")
        self.mini_panel.setToolTip("Panel prowadzącego")
        self.mini_expand = button("Pełny", lambda: self.compact.setChecked(False))
        self.mini_expand.setToolTip("Przywróć pełny widok licznika")
        for widget in (self.mini_pause, self.mini_pin, self.mini_panel, self.mini_expand):
            mini_row.addWidget(widget)
        layout.addWidget(self.mini_controls)
        self.mini_controls.hide()

    def set_pin(self, value):
        with QSignalBlocker(self.mini_pin):
            self.mini_pin.setChecked(value)
        self.mini_pin.setIcon(icon("pin", "#ffffff" if value else "#26b7a4"))
        visible, minimized = self.isVisible(), self.isMinimized()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, value)
        if visible:
            self.showMinimized() if minimized else self.show()
        self.owner.schedule_save()

    def set_compact(self, value):
        for widget in (self.position, self.bar, self.next_label, self.state, self.full_controls, self.options):
            widget.setVisible(not value)
        self.mini_controls.setVisible(value)
        self.title.setWordWrap(not value)
        self.title.setStyleSheet("font-size: 14px; font-weight: 600;" if value else "")
        self.body_layout.setContentsMargins(10, 6, 10, 6) if value else self.body_layout.setContentsMargins(28, 22, 28, 22)
        self.body_layout.setSpacing(3 if value else 14)
        self.update_digit_style()
        self.setMinimumSize(240 if value else 350, 0)
        self.resize(260 if value else 550, 138 if value else 370)
        self.update_title()
        self.owner.schedule_save()

    def update_digit_style(self):
        size = 42 if self.compact.isChecked() else 78
        self.digits.setStyleSheet(f"color: {self.time_color}; font-size: {size}px;")

    def update_title(self):
        self.title.setToolTip(self.full_title)
        if self.compact.isChecked():
            self.title.setText(self.title.fontMetrics().elidedText(self.full_title, Qt.TextElideMode.ElideRight, max(80, self.width() - 20)))
        else:
            self.title.setText(self.full_title)

    def resizeEvent(self, event):
        if hasattr(self, "compact"):
            self.update_title()
        super().resizeEvent(event)

    def update_snapshot(self, snap, items):
        if snap.index < 0:
            return
        self.position.setText(f"PUNKT {snap.index + 1} / {len(items)}")
        self.full_title = items[snap.index].title
        self.title.translate_enabled = False
        self.update_title()
        self.digits.setText(format_time(snap.remaining))
        self.time_color = "#e56c6c" if snap.remaining < 0 else "#d9922e" if snap.remaining <= 60 else "#26b7a4"
        self.update_digit_style()
        self.bar.setValue(int(snap.progress * 1000))
        states = {"ready": "Gotowy do startu", "waiting": "Do początku punktu", "running": "Do końca punktu",
                  "overtime": "Przekroczony czas", "finished": "Spotkanie zakończone"}
        self.state.setText("PAUZA · " + states.get(snap.state, "") if snap.paused else states.get(snap.state, ""))
        self.pause.setText("Start" if snap.state == "ready" else "Wznów" if snap.paused else "Pauza")
        self.pause.setEnabled(snap.state != "finished")
        self.mini_pause.setIcon(icon("player-play" if snap.paused or snap.state == "ready" else "player-pause"))
        self.mini_pause.setToolTip(self.pause.text())
        self.mini_pause.setAccessibleName(self.pause.text())
        self.mini_pause.setEnabled(self.pause.isEnabled())
        self.next_label.setText("Dalej: " + items[snap.index + 1].title if snap.index + 1 < len(items) else "Ostatni punkt agendy")

    def closeEvent(self, event):
        if self.owner.quitting:
            event.accept()
            return
        # Closing the shared view always leaves an accessible presenter window.
        self.hide()
        self.owner.present()
        event.ignore()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStatusBar(StatusBar(self))
        self.setWindowTitle(f"Licznik spotkaniowy · {version()} · Panel prowadzącego")
        self.setWindowIcon(icon("app"))
        self.resize(1120, 760)
        self.meeting = Meeting()
        self.engine = TimerEngine(self.meeting.items)
        self.directory = data_directory()
        self.session_path = self.directory / "session.json"
        self.selected_id = None
        self.loading = False
        self.quitting = False
        self.recorder = None
        self.audio_panel = None
        self.screenshots_dialog = None
        self.last_snapshot = None
        self.last_marker_id = None
        self.last_saved = 0
        self.error_shown = False
        app = QApplication.instance()
        install(app)
        self.system_palette = getattr(app, "system_palette", app.palette())
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(700)
        self.save_timer.timeout.connect(self.save_session)
        self.build_ui()
        self.counter = CounterWindow(self)
        self.build_menu()
        self.build_tray()
        app.styleHints().colorSchemeChanged.connect(self.system_scheme_changed)
        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(250)
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.start()
        self.refresh_list()
        self.tick()

    def build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(13)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("Spotkanie pod kontrolą", "brand"))
        titles.addWidget(label("Agenda, czas i ustalenia — w jednym miejscu.", "subtitle"))
        header.addLayout(titles)
        header.addStretch()
        self.theme = ComboBox()
        self.theme.addItems(["Motyw systemowy", "Jasny", "Ciemny"])
        self.theme.currentIndexChanged.connect(self.change_theme)
        header.addWidget(self.theme)
        self.language_combo = ComboBox()
        for code, native_name in LANGUAGES.items():
            self.language_combo.addItem(native_name, code)
        self.language_combo.setCurrentIndex(list(LANGUAGES).index(language()))
        self.language_combo.setToolTip("Język interfejsu")
        self.language_combo.currentIndexChanged.connect(self.change_language)
        header.addWidget(self.language_combo)
        header.addWidget(button("Pokaż licznik", self.show_counter, "clock", True))
        layout.addLayout(header)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        agenda = QWidget()
        agenda_layout = QVBoxLayout(agenda)
        agenda_layout.setContentsMargins(0, 0, 8, 0)
        top = QHBoxLayout()
        top.addWidget(label("Agenda", "section"))
        top.addStretch()
        top.addWidget(button("Wklej", self.paste_agenda, "notes"))
        agenda_layout.addLayout(top)
        self.agenda_list = QListWidget()
        self.agenda_list.currentRowChanged.connect(self.select_row)
        agenda_layout.addWidget(self.agenda_list)
        actions = QHBoxLayout()
        for text, callback, image in [("Dodaj", self.add_item, "plus"),
                                      ("↑", lambda: self.move_item(-1), "arrow-up"),
                                      ("↓", lambda: self.move_item(1), "arrow-down"),
                                      ("Usuń", self.delete_item, "trash")]:
            actions.addWidget(button(text, callback, image))
        agenda_layout.addLayout(actions)
        agenda_layout.addWidget(button("Przejdź do wybranego punktu", self.jump_selected, "player-skip-forward"))
        self.splitter.addWidget(agenda)
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(8, 0, 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Tytuł punktu")
        self.title_edit.textEdited.connect(self.edit_title)
        detail_layout.addWidget(self.title_edit)
        times = QHBoxLayout()
        times.addWidget(label("Czas punktu (sekundy):", "muted"))
        self.duration = QSpinBox()
        self.duration.setRange(1, 604800)
        self.duration.setSingleStep(60)
        self.duration.editingFinished.connect(self.edit_duration)
        times.addWidget(self.duration)
        times.addStretch()
        detail_layout.addLayout(times)
        self.tabs = QTabWidget()
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText("Przygotuj notatki przed spotkaniem lub zapisuj je w trakcie…")
        self.decisions = QPlainTextEdit()
        self.decisions.setPlaceholderText("Jakie decyzje podjęliście?")
        self.notes.textChanged.connect(self.edit_notes)
        self.decisions.textChanged.connect(self.edit_notes)
        self.tabs.addTab(self.notes, "Notatki")
        self.tabs.addTab(self.decisions, "Decyzje")
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        self.tasks = QTableWidget(0, 4)
        self.tasks.setHorizontalHeaderLabels(["✓", "Zadanie", "Kto", "Do kiedy"])
        self.tasks.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tasks.setColumnWidth(0, 32)
        self.tasks.setColumnWidth(2, 100)
        self.tasks.setColumnWidth(3, 100)
        self.tasks.cellChanged.connect(self.edit_tasks)
        tasks_layout.addWidget(self.tasks)
        task_actions = QHBoxLayout()
        task_actions.addWidget(button("Dodaj zadanie", self.add_task, "plus"))
        task_actions.addWidget(button("Usuń zadanie", self.remove_task, "trash"))
        tasks_layout.addLayout(task_actions)
        self.tabs.addTab(tasks_widget, "Zadania")
        attachments = QWidget()
        attachment_layout = QVBoxLayout(attachments)
        attachment_layout.addWidget(label("Znaczniki wybranego punktu w lokalnych nagraniach. Czas oznacza pozycję w pliku.", "muted"))
        self.markers = QTableWidget(0, 3)
        self.markers.setHorizontalHeaderLabels(["Pozycja", "Punkt", "Plik"])
        self.markers.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.markers.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.markers.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        attachment_layout.addWidget(self.markers)
        attachment_layout.addWidget(button("Otwórz wybrane nagranie", self.open_recording))
        self.tabs.addTab(attachments, "Nagrania")
        self.marker_signature = None
        screenshots_widget = QWidget()
        screenshot_layout = QVBoxLayout(screenshots_widget)
        self.screenshot_table = QTableWidget(0, 2)
        self.screenshot_table.setHorizontalHeaderLabels(["Wykonano", "Plik zrzutu wybranego punktu"])
        self.screenshot_table.horizontalHeader().setStretchLastSection(True)
        self.screenshot_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.screenshot_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        screenshot_layout.addWidget(self.screenshot_table)
        screenshot_layout.addWidget(button("Otwórz wybrany zrzut", self.open_screenshot))
        self.tabs.addTab(screenshots_widget, "Zrzuty")
        self.screenshot_signature = None
        detail_layout.addWidget(self.tabs)
        self.splitter.addWidget(detail)
        self.splitter.setSizes([350, 670])
        layout.addWidget(self.splitter, 1)
        self.detail = detail
        plan = QHBoxLayout()
        self.mode = ComboBox()
        self.mode.addItems(["Plan od teraz", "Według godzin agendy", "Start o wskazanej godzinie"])
        self.mode.currentIndexChanged.connect(self.update_start_mode)
        plan.addWidget(self.mode)
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.setToolTip("Data rozpoczęcia harmonogramu godzinowego; kolejne punkty mogą wypaść po północy.")
        plan.addWidget(self.date)
        self.scheduled_start = QDateTimeEdit(QDateTime.currentDateTime().addSecs(300))
        self.scheduled_start.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.scheduled_start.setCalendarPopup(True)
        self.scheduled_start.setToolTip("Data i godzina rozpoczęcia całego planu")
        self.scheduled_start.dateTimeChanged.connect(self.schedule_save)
        plan.addWidget(self.scheduled_start)
        self.update_start_mode()
        self.auto = QCheckBox("Automatyczne przejścia")
        self.auto.setChecked(True)
        self.auto.toggled.connect(self.set_auto)
        plan.addWidget(self.auto)
        self.beep = QCheckBox("Sygnał końca")
        self.beep.toggled.connect(self.schedule_save)
        plan.addWidget(self.beep)
        plan.addStretch()
        layout.addLayout(plan)
        controls = QGroupBox("Sterowanie spotkaniem")
        control_layout = QVBoxLayout(controls)
        row = QHBoxLayout()
        row.addWidget(button("Poprzedni", lambda: self.step(-1), "player-skip-back"))
        self.play = button("Rozpocznij", self.play_pause, "player-play", True)
        row.addWidget(self.play)
        row.addWidget(button("Następny", lambda: self.step(1), "player-skip-forward"))
        row.addWidget(button("+1 min", lambda: self.add_time(60)))
        row.addWidget(button("+5 min", lambda: self.add_time(300)))
        row.addStretch()
        self.time_label = label("00:00", "section")
        row.addWidget(self.time_label)
        control_layout.addLayout(row)
        self.plan_label = label("Wklej agendę, aby zacząć.", "muted")
        self.plan_label.setWordWrap(True)
        control_layout.addWidget(self.plan_label)
        layout.addWidget(controls)
        bottom = QHBoxLayout()
        self.audio_toggle = button("Nagrywanie i transkrypcja ▸", self.toggle_audio, "microphone")
        bottom.addWidget(self.audio_toggle)
        bottom.addWidget(button("Zrzuty…", self.show_screenshots))
        self.screenshot_status = label("", "warning")
        bottom.addWidget(self.screenshot_status)
        self.recording_label = label("", "warning")
        bottom.addWidget(self.recording_label)
        bottom.addStretch()
        bottom.addWidget(button("Eksport", self.export, "download"))
        bottom.addWidget(button("Schowaj do zasobnika", lambda: self.hide_to_tray(self)))
        layout.addLayout(bottom)
        self.audio_container = QVBoxLayout()
        layout.addLayout(self.audio_container)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setWidget(root)
        self.setCentralWidget(self.scroll)
        self.statusBar().showMessage("Dane są zapisywane lokalnie.")
        version_label = label(version(), "muted")
        version_label.setToolTip("Commit: " + build_info()["commit"] + "\n* oznacza niezacommitowane zmiany.")
        version_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.statusBar().addPermanentWidget(version_label)

    def build_menu(self):
        from .shortcuts import ShortcutSettings
        self.shortcuts = ShortcutSettings(self.directory / "shortcuts.json")

        def add_action(menu, name, title, callback, shortcut=""):
            action = QAction(title, self)
            action.triggered.connect(callback)
            menu.addAction(action)
            self.addAction(action)
            self.counter.addAction(action)
            self.shortcuts.register(name, action, shortcut)
            return action

        menu = self.menuBar().addMenu("Spotkanie")
        for name, title, callback, shortcut in [
            ("paste", "Wklej agendę…", self.paste_agenda, "Ctrl+N"),
            ("open", "Otwórz plik spotkania…", self.open_meeting, "Ctrl+O"),
            ("save", "Zapisz kopię spotkania…", self.save_copy, "Ctrl+S"),
            ("save_template", "Zapisz szablon…", self.save_template, ""),
            ("load_template", "Wczytaj szablon…", self.open_meeting, ""),
            ("export", "Eksport podsumowania…", self.export, "Ctrl+E"),
            ("restart", "Restart odliczania…", self.restart, ""),
            ("data", "Otwórz katalog danych", self.open_data_directory, ""),
            ("quit", "Zakończ", self.quit, "Ctrl+Q")]:
            add_action(menu, name, title, callback, shortcut)
        controls = self.menuBar().addMenu("Sterowanie")
        for name, title, callback, shortcut in [
            ("play", "Start / pauza / wznów", self.play_pause, "Ctrl+Return"),
            ("previous", "Poprzedni punkt", lambda: self.step(-1), "Ctrl+Alt+Left"),
            ("next", "Następny punkt", lambda: self.step(1), "Ctrl+Alt+Right"),
            ("add_minute", "+1 min", lambda: self.add_time(60), "Ctrl+Alt+1"),
            ("add_five", "+5 min", lambda: self.add_time(300), "Ctrl+Alt+5"),
            ("counter", "Pokaż licznik", self.show_counter, "Ctrl+L"),
            ("presenter", "Pokaż panel", self.present, ""),
            ("pin", "Zawsze na wierzchu", self.counter.pin.toggle, "Ctrl+Shift+T"),
            ("compact", "Widok kompaktowy", self.counter.compact.toggle, "Ctrl+Shift+M")]:
            add_action(controls, name, title, callback, shortcut)
        self.help_menu = self.menuBar().addMenu("Pomoc")
        for name, title, callback, shortcut in [
            ("help", "Instrukcja obsługi", self.show_help, "F1"),
            ("shortcuts", "Skróty klawiaturowe…", self.configure_shortcuts, ""),
            ("feedback", "Zgłoś błąd / Przekaż opinię", self.open_feedback, ""),
            ("project", "Strona projektu", self.open_project, ""),
            ("terms", "Warunki użytkowania", self.show_terms, ""),
            ("license", "Licencja MIT", lambda: self.show_document("LICENSE", "Licencja MIT", True), ""),
            ("privacy", "Polityka prywatności (PL)", lambda: self.show_document("PRIVACY.md", "Polityka prywatności (PL)"), ""),
            ("support", "Postaw mi kawę · Buy me a coffee", self.open_support, "")]:
            add_action(self.help_menu, name, title, callback, shortcut)
        if not self.shortcuts.load():
            self.statusBar().showMessage("Nie można odczytać skrótów — użyto domyślnych.")

    def build_tray(self):
        self.tray = QSystemTrayIcon(icon("clock"), self)
        self.tray.setToolTip("Licznik spotkaniowy")
        self.tray_menu = QMenu(self)
        for text, callback in [("Pokaż panel", self.present), ("Pokaż licznik", self.show_counter),
                               ("Start / pauza / wznów", self.play_pause),
                               ("Zrzuty ekranu…", self.show_screenshots), ("Zakończ", self.quit)]:
            action = self.tray_menu.addAction(text)
            action.triggered.connect(callback)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(lambda reason: self.present() if reason in
                                   (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick) else None)
        self.tray.show()

    def present(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def show_counter(self):
        self.counter.showNormal()
        self.counter.raise_()
        self.counter.activateWindow()

    def hide_to_tray(self, window):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.statusBar().showMessage("Zasobnik niedostępny — okno zminimalizowano do paska.", 6000)
            window.showMinimized()
            return
        window.hide()
        self.tray.showMessage("Licznik działa w tle", "Kliknij ikonę zegara w zasobniku, aby wrócić.",
                              QSystemTrayIcon.MessageIcon.Information, 2500)

    def selected_item(self):
        return next((i for i in self.meeting.items if i.id == self.selected_id), None)

    def refresh_list(self):
        self.active_list_key = None
        selected = self.selected_id
        with QSignalBlocker(self.agenda_list):
            self.agenda_list.clear()
            for index, item in enumerate(self.meeting.items):
                self.agenda_list.addItem(f"{index + 1:02}   {item.title}   ·   {format_time(item.seconds)}")
            row = next((i for i, item in enumerate(self.meeting.items) if item.id == selected), 0)
            self.agenda_list.setCurrentRow(row if self.meeting.items else -1)
        self.select_row(self.agenda_list.currentRow())

    def select_row(self, row):
        self.loading = True
        item = self.meeting.items[row] if 0 <= row < len(self.meeting.items) else None
        self.selected_id = item.id if item else None
        self.detail.setEnabled(item is not None)
        self.title_edit.setText(item.title if item else "")
        self.duration.setValue(item.seconds if item else 60)
        self.notes.setPlainText(item.notes if item else "")
        self.decisions.setPlainText(item.decisions if item else "")
        self.tasks.setRowCount(0)
        if item:
            for task in item.tasks:
                self.append_task_row(task)
        self.refresh_markers()
        self.refresh_screenshots()
        self.loading = False

    def refresh_screenshots(self):
        rows = [entry for entry in self.meeting.screenshots if entry.get("item_id") == self.selected_id]
        signature = repr(rows)
        if signature == self.screenshot_signature:
            return
        self.screenshot_signature = signature
        self.screenshot_table.setRowCount(len(rows))
        for row, entry in enumerate(rows):
            try:
                timestamp = datetime.fromtimestamp(float(entry.get("created_at", 0))).strftime("%H:%M:%S")
            except (TypeError, ValueError, OverflowError, OSError):
                timestamp = "?"
            path = str(entry.get("path", ""))
            for col, text in enumerate((timestamp, Path(path).name)):
                cell = QTableWidgetItem(text)
                cell.setData(Qt.ItemDataRole.UserRole, path)
                self.screenshot_table.setItem(row, col, cell)

    def open_screenshot(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        cell = self.screenshot_table.item(self.screenshot_table.currentRow(), 0)
        if cell:
            path = Path(cell.data(Qt.ItemDataRole.UserRole))
            if path.is_file() and path.suffix.lower() == ".png":
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            else:
                self.message("Brak zrzutu", "Plik PNG przeniesiono lub usunięto.")

    def refresh_markers(self):
        rows = []
        for recording in self.meeting.recordings:
            for marker in recording.get("markers", []):
                if isinstance(marker, dict) and marker.get("item_id") == self.selected_id:
                    rows.append((marker.get("seconds", 0), marker.get("title", ""), recording.get("path", "")))
        signature = repr(rows)
        if signature == self.marker_signature:
            return
        self.marker_signature = signature
        self.markers.setRowCount(len(rows))
        for row, (seconds, title, path) in enumerate(rows):
            try:
                position = format_time(float(seconds))
            except (TypeError, ValueError, OverflowError):
                position = "?"
            for col, text in enumerate((position, str(title), Path(str(path)).name)):
                cell = QTableWidgetItem(text)
                cell.setData(Qt.ItemDataRole.UserRole, str(path))
                self.markers.setItem(row, col, cell)

    def open_recording(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        cell = self.markers.item(self.markers.currentRow(), 0)
        if cell:
            path = Path(cell.data(Qt.ItemDataRole.UserRole))
            if path.is_file() and path.suffix.lower() in (".wav", ".mp3", ".m4a", ".webm", ".mp4", ".mpeg", ".mpga"):
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            else:
                self.message("Brak nagrania", "Plik przeniesiono lub usunięto. Kopia JSON zawiera odnośniki, a nie nagrania.")

    def append_task_row(self, task):
        row = self.tasks.rowCount()
        self.tasks.insertRow(row)
        check = QTableWidgetItem()
        check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        check.setCheckState(Qt.CheckState.Checked if task.done else Qt.CheckState.Unchecked)
        self.tasks.setItem(row, 0, check)
        for col, value in enumerate((task.text, task.owner, task.due), 1):
            self.tasks.setItem(row, col, QTableWidgetItem(value))

    def edit_title(self, text):
        if item := self.selected_item():
            item.title = text.strip() or "Bez tytułu"
            row = self.agenda_list.currentRow()
            self.agenda_list.item(row).setText(f"{row + 1:02}   {item.title}   ·   {format_time(item.seconds)}")
            self.schedule_save()

    def edit_duration(self):
        if not self.loading and (item := self.selected_item()):
            self.engine.mutate(lambda: setattr(item, "seconds", self.duration.value()))
            self.refresh_list()
            self.schedule_save()

    def edit_notes(self):
        if not self.loading and (item := self.selected_item()):
            item.notes = self.notes.toPlainText()
            item.decisions = self.decisions.toPlainText()
            self.schedule_save()

    def edit_tasks(self, *_):
        if self.loading or not (item := self.selected_item()):
            return
        tasks = []
        for row in range(self.tasks.rowCount()):
            values = [self.tasks.item(row, col) for col in range(4)]
            if all(v is not None for v in values):
                tasks.append(Task(values[1].text(), values[2].text(), values[3].text(),
                                  values[0].checkState() == Qt.CheckState.Checked))
        item.tasks = tasks
        self.schedule_save()

    def add_task(self):
        if not self.selected_item():
            return
        self.loading = True
        self.append_task_row(Task())
        self.loading = False
        self.edit_tasks()

    def remove_task(self):
        if self.tasks.currentRow() >= 0:
            self.loading = True
            self.tasks.removeRow(self.tasks.currentRow())
            self.loading = False
            self.edit_tasks()

    def paste_agenda(self):
        dialog = AgendaDialog(self, replacing=bool(self.meeting.items))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.replace_items(dialog.items)

    def replace_items(self, items):
        self.meeting.removed.extend(self.meeting.items)
        self.meeting.items = items
        self.engine = TimerEngine(items)
        self.engine.auto = self.auto.isChecked()
        self.mode.setEnabled(True)
        self.date.setEnabled(True)
        self.scheduled_start.setEnabled(True)
        self.selected_id = None
        self.last_snapshot = None
        self.last_marker_id = None
        self.refresh_list()
        self.schedule_save()
        self.tick()

    def add_item(self):
        title, ok = QInputDialog.getText(self, "Nowy punkt", "Tytuł:")
        if ok and title.strip():
            item = Item(title.strip(), 300)
            self.engine.mutate(lambda: self.meeting.items.append(item))
            self.selected_id = item.id
            self.refresh_list()
            self.schedule_save()

    def move_item(self, direction):
        index = self.agenda_list.currentRow()
        target = index + direction
        if not 0 <= target < len(self.meeting.items):
            return
        snap = self.engine.snapshot()
        if self.engine.started and min(index, target) <= snap.index:
            self.message("Zmiana kolejności", "W trakcie można przestawiać przyszłe punkty. Bieżący i przebyte punkty zachowują kolejność; możesz edytować ich treść lub do nich przejść.")
            return
        def operation():
            self.meeting.items[index], self.meeting.items[target] = self.meeting.items[target], self.meeting.items[index]
        self.engine.mutate(operation)
        self.refresh_list()
        self.schedule_save()

    def delete_item(self):
        item = self.selected_item()
        if not item:
            return
        index = self.agenda_list.currentRow()
        snap = self.engine.snapshot()
        if self.engine.started and item.id == self.engine.current_id:
            candidates = [i for i in self.meeting.items if i.id != item.id]
            if not candidates:
                self.message("Usuwanie punktu", "Najpierw zatrzymaj spotkanie (Restart) lub dodaj punkt, który ma go zastąpić.")
                return
            choices = [f"{n + 1}. {i.title}" for n, i in enumerate(candidates)]
            choice, ok = QInputDialog.getItem(self, "Usuń bieżący punkt", "Wybierz następcę. Notatki usuniętego punktu pozostaną w pliku sesji.", choices, 0, False)
            if not ok:
                return
            successor = candidates[choices.index(choice)].id
        else:
            if QMessageBox.question(self, "Usuń punkt", "Usunąć punkt z agendy? Jego dane pozostaną w pliku bieżącej sesji.") != QMessageBox.StandardButton.Yes:
                return
            successor = None
        self.engine.mutate(lambda: self.meeting.removed.append(self.meeting.items.pop(index)))
        if successor:
            self.engine.jump(next(n for n, i in enumerate(self.meeting.items) if i.id == successor))
        elif snap.index == index and not self.engine.started and self.meeting.items:
            self.engine.current_id = self.meeting.items[0].id
        self.refresh_list()
        self.schedule_save()

    def jump_selected(self):
        if self.agenda_list.currentRow() >= 0:
            self.engine.jump(self.agenda_list.currentRow())
            self.last_marker_id = None
            self.schedule_save()
            self.tick()

    def step(self, delta):
        snap = self.engine.snapshot()
        self.engine.jump(snap.index + delta)
        self.last_marker_id = None
        self.schedule_save()
        self.tick()

    def add_time(self, seconds):
        self.engine.add_time(seconds)
        self.refresh_list()
        self.schedule_save()
        self.tick()

    def set_auto(self, value):
        self.engine.auto = value
        self.schedule_save()

    def update_start_mode(self, *_):
        if hasattr(self, "scheduled_start"):
            self.date.setVisible(self.mode.currentIndex() == 1)
            self.scheduled_start.setVisible(self.mode.currentIndex() == 2)
        self.schedule_save()

    def play_pause(self):
        if not self.meeting.items:
            self.paste_agenda()
            return
        if not self.engine.started:
            epoch = None
            if self.mode.currentIndex() == 1:
                if self.meeting.items[0].scheduled is None:
                    self.message("Brak godzin", "Ta agenda zawiera czasy trwania. Wybierz „Plan od teraz”.")
                    return
                day = self.date.date().toPython()
                epoch = (datetime(day.year, day.month, day.day) + timedelta(seconds=self.meeting.items[0].scheduled)).timestamp()
            elif self.mode.currentIndex() == 2:
                epoch = self.scheduled_start.dateTime().toSecsSinceEpoch()
            self.engine.start(epoch)
            self.mode.setEnabled(False)
            self.date.setEnabled(False)
            self.scheduled_start.setEnabled(False)
            self.show_counter()
        else:
            self.engine.toggle_pause()
        self.schedule_save()
        self.tick()

    def restart(self):
        if QMessageBox.question(self, "Restart odliczania", "Zatrzymać odliczanie i przygotować plan do ponownego startu? Notatki zostaną zachowane, nagranie trwa niezależnie.") == QMessageBox.StandardButton.Yes:
            self.engine = TimerEngine(self.meeting.items)
            self.engine.auto = self.auto.isChecked()
            self.mode.setEnabled(True)
            self.date.setEnabled(True)
            self.scheduled_start.setEnabled(True)
            self.last_marker_id = None
            self.schedule_save()
            self.tick()

    def tick(self):
        snap = self.engine.snapshot()
        active_key = (snap.index, snap.state, self.engine.started)
        if active_key != getattr(self, "active_list_key", None):
            self.active_list_key = active_key
            for index, item in enumerate(self.meeting.items):
                prefix = "● " if index == snap.index and self.engine.started else ""
                cell = self.agenda_list.item(index)
                if cell:
                    cell.setText(f"{prefix}{index + 1:02}   {item.title}   ·   {format_time(item.seconds)}")
        self.counter.update_snapshot(snap, self.meeting.items)
        self.play.setEnabled(snap.state != "finished")
        self.play.setText("Rozpocznij" if not self.engine.started else "Wznów" if snap.paused else "Pauza")
        self.time_label.setText(format_time(snap.remaining))
        if snap.index >= 0:
            title = self.meeting.items[snap.index].title
            states = {"ready": "Gotowy", "waiting": "Oczekiwanie", "running": "Trwa", "overtime": "Przekroczenie", "finished": "Koniec"}
            state = "Pauza" if snap.paused else states.get(snap.state, "")
            plan = f"{tr(state)} · {title}"
            if self.engine.started and snap.state != "finished":
                end = datetime.fromtimestamp(self.engine.predicted_end).strftime("%H:%M")
                delay = self.engine.predicted_end - self.engine.baseline_end if self.engine.baseline_end else 0
                plan += tr(" · koniec ok. {end} · względem planu {delta}", end=end,
                           delta=('+' if delay >= 0 else '−') + format_time(abs(delay)))
            self.plan_label.setText(plan)
            self.tray.setToolTip(f"{tr(state)} · {format_time(snap.remaining)} · {title}"[:120])
            if self.last_snapshot and self.beep.isChecked() and self.last_snapshot.state == "running" and (snap.index != self.last_snapshot.index or snap.state in ("overtime", "finished")):
                QApplication.beep()
            if self.recorder and self.recorder.active and self.engine.started:
                item = self.meeting.items[snap.index]
                if item.id != self.last_marker_id:
                    self.recorder.mark(item.id, item.title)
                    self.last_marker_id = item.id
        self.last_snapshot = snap
        if self.audio_panel:
            self.audio_panel.poll()
        self.refresh_markers()
        self.refresh_screenshots()
        if self.recorder and self.recorder.active:
            self.tray.setIcon(icon("microphone", "#e56c6c"))
        elif self.screenshots_dialog and self.screenshots_dialog.running:
            self.tray.setIcon(icon("clock", "#d9922e"))
        else:
            self.tray.setIcon(icon("clock"))
        if self.screenshots_dialog and self.screenshots_dialog.running:
            self.tray.setToolTip((self.tray.toolTip() + f" · Zrzuty co {self.screenshots_dialog.interval.value()} s")[:120])
        if self.engine.started and time.monotonic() - self.last_saved >= 5:
            self.save_session()

    def schedule_save(self, *_):
        if not self.loading:
            self.statusBar().showMessage("Zapisywanie…")
            self.save_timer.start()

    def save_session(self, clean=False):
        self.save_timer.stop()
        try:
            atomic_json(self.session_path, {
                "version": 1, "meeting": self.meeting.to_dict(), "clean": bool(clean),
                "engine": {"started": self.engine.started, "cursor": self.engine.cursor,
                           "current_id": self.engine.current_id, "auto": self.engine.auto,
                           "completed": self.engine.completed,
                           "baseline_end": self.engine.baseline_end, "gaps": self.engine.gaps},
                "preferences": {"theme": self.theme.currentIndex(), "beep": self.beep.isChecked(),
                                "pin": self.counter.pin.isChecked(), "compact": self.counter.compact.isChecked(),
                                "mode": self.mode.currentIndex(), "language": language(),
                                "scheduled_start": self.scheduled_start.dateTime().toString(Qt.DateFormat.ISODate)},
            })
            self.last_saved = time.monotonic()
            self.error_shown = False
            self.statusBar().showMessage("Zapisano lokalnie")
            return True
        except (OSError, ValueError):
            self.statusBar().showMessage("Błąd zapisu — zapisz kopię w innym katalogu przez menu Spotkanie.")
            if not self.error_shown:
                self.error_shown = True
                self.message("Nie można zapisać", "Sprawdź wolne miejsce i prawa zapisu. Dane pozostają w pamięci; zapisz kopię spotkania przed zamknięciem.")
            return False

    def restore(self):
        if not self.session_path.exists():
            return
        try:
            data = read_json(self.session_path)
            meeting = Meeting.from_dict(data["meeting"])
            if not data.get("clean", False):
                answer = QMessageBox.question(self, "Odzyskać spotkanie?", "Poprzednia sesja nie została zamknięta poprawnie. Odzyskać agendę i notatki? Licznik wróci w pauzie; nagrywanie i API nie zostaną uruchomione.")
                if answer != QMessageBox.StandardButton.Yes:
                    atomic_json(self.directory / "session-discarded.json", data)
                    return
            self.loading = True
            self.meeting = meeting
            self.engine = TimerEngine(meeting.items)
            prefs, state = data.get("preferences", {}), data.get("engine", {})
            cursor = float(state.get("cursor", 0))
            if not math.isfinite(cursor) or abs(cursor) > 1_000_000_000:
                raise ValueError("Nieprawidłowa pozycja licznika.")
            self.theme.setCurrentIndex(max(0, min(2, int(prefs.get("theme", 0)))))
            self.beep.setChecked(bool(prefs.get("beep", False)))
            self.counter.pin.setChecked(bool(prefs.get("pin", False)))
            self.counter.compact.setChecked(bool(prefs.get("compact", False)))
            self.mode.setCurrentIndex(max(0, min(2, int(prefs.get("mode", 0)))))
            saved_start = QDateTime.fromString(prefs.get("scheduled_start", ""), Qt.DateFormat.ISODate)
            if saved_start.isValid():
                self.scheduled_start.setDateTime(saved_start)
            language_code = prefs.get("language", "pl")
            self.language_combo.setCurrentIndex(list(LANGUAGES).index(language_code) if language_code in LANGUAGES else 0)
            self.auto.setChecked(bool(state.get("auto", True)))
            self.engine.auto = self.auto.isChecked()
            if not data.get("clean") and state.get("started"):
                self.engine.started = self.engine.paused = True
                self.engine.completed = bool(state.get("completed", False))
                self.engine.seek(cursor)
                self.engine.current_id = str(state.get("current_id", ""))
                baseline = state.get("baseline_end")
                self.engine.baseline_end = float(baseline) if baseline is not None else None
                if self.engine.baseline_end is not None and not math.isfinite(self.engine.baseline_end):
                    raise ValueError("Nieprawidłowy plan końca.")
                self.mode.setEnabled(False)
                self.date.setEnabled(False)
                self.scheduled_start.setEnabled(False)
            gaps = state.get("gaps", {})
            self.engine.gaps = {str(k): max(0, int(v)) for k, v in gaps.items()}
            self.refresh_list()
            self.loading = False
            self.tick()
        except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
            self.loading = False
            self.engine = TimerEngine(self.meeting.items)
            self.engine.auto = self.auto.isChecked()
            self.mode.setEnabled(True)
            self.date.setEnabled(True)
            self.scheduled_start.setEnabled(True)
            backup = self.session_path.with_name(f"session-damaged-{time.time_ns()}.json")
            try:
                self.session_path.rename(backup)
            except OSError:
                self.message("Błąd odzyskiwania", "Plik sesji jest nieczytelny i nie udało się zachować kopii. Nie zostanie nadpisany; zmień katalog danych przed dalszą pracą.")
                self.session_path = self.directory / f"session-new-{time.time_ns()}.json"
                return
            self.message("Błąd odzyskiwania", f"Nieczytelny plik zachowano jako {backup.name}. Możesz rozpocząć nowe spotkanie.")

    def open_meeting(self):
        if self.screenshots_dialog and (self.screenshots_dialog.running or self.screenshots_dialog.busy):
            self.message("Trwa zapisywanie zrzutów", "Przed otwarciem innego spotkania zatrzymaj zrzuty i poczekaj na zapis obrazu.")
            return
        if self.audio_panel and self.audio_panel.busy:
            self.message("Trwa zadanie", "Przed otwarciem innego pliku zakończ nagranie lub zadanie API. Edytowanie obecnej agendy i notatek jest nadal dostępne.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Otwórz spotkanie lub szablon", str(self.directory), "Spotkanie (*.json)")
        if not path:
            return
        try:
            meeting = load_meeting(path)
        except (OSError, ValueError, TypeError, KeyError):
            self.message("Błąd pliku", "Nie można odczytać spotkania. Obecne dane pozostają bez zmian.")
            return
        if self.meeting.items and QMessageBox.question(self, "Zastąpić spotkanie?", "Obecna agenda zostanie zastąpiona. Najpierw zapisz kopię, jeśli chcesz ją zachować. Nagranie trwa niezależnie.") != QMessageBox.StandardButton.Yes:
            return
        try:
            if self.meeting.items:
                save_meeting(self.directory / "session-before-open.json", self.meeting)
        except OSError:
            self.message("Błąd zapisu", "Nie można zachować kopii obecnej sesji. Otwarcie pliku przerwano.")
            return
        self.meeting = meeting
        if self.audio_panel:
            self.audio_panel.reload_transcripts()
        self.engine = TimerEngine(meeting.items)
        self.engine.auto = self.auto.isChecked()
        self.mode.setEnabled(True)
        self.date.setEnabled(True)
        self.scheduled_start.setEnabled(True)
        self.selected_id = None
        self.last_snapshot = self.last_marker_id = None
        self.refresh_list()
        self.schedule_save()
        self.tick()

    def save_copy(self):
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz kopię spotkania", "spotkanie.json", "Spotkanie (*.json)")
        if path:
            try:
                save_meeting(path, self.meeting)
            except (OSError, ValueError):
                self.message("Błąd zapisu", "Nie udało się zapisać kopii.")

    def save_template(self):
        include = QMessageBox.question(self, "Szablon", "Dołączyć notatki przygotowawcze? Decyzje, zadania, nagrania i transkrypcje nie trafią do szablonu.") == QMessageBox.StandardButton.Yes
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz szablon", "szablon.json", "Szablon (*.json)")
        if path:
            try:
                atomic_json(Path(path), template_data(self.meeting, include))
            except (OSError, ValueError):
                self.message("Błąd zapisu", "Nie udało się zapisać szablonu.")

    def export(self):
        dialog = ExportDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        path, selected = QFileDialog.getSaveFileName(self, "Eksport podsumowania", "podsumowanie.md", "Markdown (*.md);;PDF (*.pdf)")
        if not path:
            return
        try:
            if "PDF" in selected:
                if not path.lower().endswith(".pdf"):
                    path += ".pdf"
                writer = QPdfWriter(path)
                writer.setTitle("Podsumowanie spotkania")
                pdf_document(self.meeting, **dialog.options()).print_(writer)
                if not Path(path).exists() or Path(path).stat().st_size == 0:
                    raise OSError("Empty PDF")
            else:
                Path(path).write_text(markdown(self.meeting, **dialog.options()), encoding="utf-8")
            self.statusBar().showMessage("Wyeksportowano podsumowanie.", 5000)
        except (OSError, ValueError):
            self.message("Błąd eksportu", "Nie udało się zapisać podsumowania. Sprawdź katalog i wolne miejsce.")

    def toggle_audio(self):
        if self.audio_panel is None:
            from .audio_ui import AudioPanel
            self.audio_panel = AudioPanel(self)
            self.audio_container.addWidget(self.audio_panel)
            self.audio_panel.show()
        else:
            self.audio_panel.setVisible(not self.audio_panel.isVisible())
        self.audio_toggle.setText("Nagrywanie i transkrypcja ▾" if not self.audio_panel.isHidden() else "Nagrywanie i transkrypcja ▸")

    def show_screenshots(self):
        if self.screenshots_dialog is None:
            from .capture import ScreenshotDialog
            self.screenshots_dialog = ScreenshotDialog(self)
        self.screenshots_dialog.show()
        self.screenshots_dialog.raise_()
        self.screenshots_dialog.activateWindow()

    def change_theme(self, index):
        apply_theme(QApplication.instance(), ["system", "light", "dark"][index], self.system_palette)
        self.schedule_save()

    def change_language(self, _index):
        set_language(self.language_combo.currentData())
        self.tick()
        self.schedule_save()

    def system_scheme_changed(self, _scheme):
        if self.theme.currentIndex() == 0:
            apply_theme(QApplication.instance(), "system", self.system_palette)

    def open_data_directory(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        self.directory.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.directory)))

    def show_help(self):
        from .documents import HelpDialog
        try:
            HelpDialog(self).exec()
        except OSError:
            self.message("Błąd pliku", "Nie można odczytać dokumentu pomocy.")

    def configure_shortcuts(self):
        from .shortcuts import ShortcutsDialog
        ShortcutsDialog(self.shortcuts, self).exec()

    def open_feedback(self):
        from .documents import FEEDBACK_URL
        self.open_link(FEEDBACK_URL)

    def open_project(self):
        from .documents import PROJECT_URL, PROJECT_URL_EN
        self.open_link(PROJECT_URL if language() == "pl" else PROJECT_URL_EN)

    def open_link(self, url):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(url))

    def show_terms(self):
        from .documents import DocumentDialog, terms_text
        DocumentDialog("Warunki użytkowania", terms_text(), self).exec()

    def show_document(self, name, title, plain=False):
        from .documents import DocumentDialog, document_text
        try:
            text = document_text(name)
        except OSError:
            self.message("Błąd pliku", "Nie można odczytać dokumentu pomocy.")
            return
        DocumentDialog(title, text, self, plain=plain).exec()

    def open_support(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        from .documents import SUPPORT_URL
        QDesktopServices.openUrl(QUrl(SUPPORT_URL))

    def message(self, title, text):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText(text)
        box.exec()

    def quit(self):
        if self.screenshots_dialog:
            self.screenshots_dialog.stop()
            if self.screenshots_dialog.busy:
                self.message("Trwa zapis zrzutu", "Zatrzymano cykl zrzutów. Poczekaj na zakończenie zapisu i ponownie wybierz Zakończ.")
                return
        if self.audio_panel and self.audio_panel.busy:
            self.message("Trwa zadanie", "Najpierw zatrzymaj nagranie i zakończ lub anuluj transkrypcję. Poczekaj na zapis pliku.")
            self.present()
            return
        if not self.save_session(clean=True):
            return
        self.quitting = True
        self.tray.hide()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self.quitting:
            event.accept()
            return
        box = QMessageBox(self)
        box.setWindowTitle("Zamknąć program?")
        box.setText("Możesz schować panel i kontynuować spotkanie w tle lub zakończyć program.")
        hide = box.addButton("Schowaj", QMessageBox.ButtonRole.ActionRole)
        finish = box.addButton("Zakończ", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()
        event.ignore()
        if box.clickedButton() == hide:
            self.hide_to_tray(self)
        elif box.clickedButton() == finish:
            self.quit()

    def resizeEvent(self, event):
        if hasattr(self, "splitter"):
            self.splitter.setOrientation(Qt.Orientation.Vertical if self.width() < 850 else Qt.Orientation.Horizontal)
        super().resizeEvent(event)
