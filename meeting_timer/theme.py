"""Small native widget theme, with bundled SVG icons; no theme framework."""

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).parent / "assets"


@lru_cache(maxsize=64)
def icon(name, color="#26b7a4"):
    path = ASSETS / f"{name}.svg"
    if not path.exists():
        return QIcon()
    renderer = QSvgRenderer(path.read_bytes().replace(b"currentColor", color.encode()))
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def apply_theme(app, mode="system", system_palette=None):
    system_palette = system_palette or QPalette()
    dark = mode == "dark" or (mode == "system" and system_palette.color(QPalette.ColorRole.Window).lightness() < 128)
    bg, panel, field, text, muted, border = (
        ("#111b23", "#192630", "#13202a", "#edf4f6", "#9bafba", "#31434e") if dark else
        ("#f2f6f7", "#ffffff", "#f8fafb", "#192d39", "#5a707e", "#d4e0e5")
    )
    palette = QPalette(system_palette)
    for role, value in [(QPalette.ColorRole.Window, bg), (QPalette.ColorRole.WindowText, text),
                        (QPalette.ColorRole.Base, field), (QPalette.ColorRole.AlternateBase, panel),
                        (QPalette.ColorRole.Text, text), (QPalette.ColorRole.Button, panel),
                        (QPalette.ColorRole.ButtonText, text), (QPalette.ColorRole.Highlight, "#168f83"),
                        (QPalette.ColorRole.HighlightedText, "#ffffff")]:
        palette.setColor(role, QColor(value))
    app.setPalette(palette)
    app.setStyleSheet(f"""
        QWidget {{ font-size: 13px; }}
        QMainWindow, QWidget#counter {{ background: {bg}; }}
        QLabel#brand {{ font-size: 25px; font-weight: 700; }}
        QLabel#subtitle, QLabel#muted {{ color: {muted}; }}
        QLabel#section {{ font-size: 17px; font-weight: 600; }}
        QLabel#digits {{ font-size: 78px; font-weight: 700; color: #26b7a4; }}
        QLabel#counterTitle {{ font-size: 23px; font-weight: 600; }}
        QLabel#warning {{ color: #d9922e; }}
        QGroupBox {{ border: 1px solid {border}; border-radius: 9px; margin-top: 12px; padding: 14px; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; }}
        QPushButton {{ background: {panel}; border: 1px solid {border}; border-radius: 6px; padding: 7px 10px; }}
        QPushButton:hover {{ border-color: #26b7a4; }}
        QPushButton:pressed {{ background: #168f83; color: white; }}
        QPushButton:disabled {{ color: {muted}; }}
        QPushButton#primary {{ background: #168f83; border-color: #168f83; color: white; font-weight: 600; }}
        QLineEdit, QPlainTextEdit, QTextEdit, QListWidget, QTableWidget, QComboBox, QSpinBox, QDateEdit {{
            background: {field}; border: 1px solid {border}; border-radius: 5px; padding: 5px;
        }}
        QListWidget::item {{ padding: 10px 8px; margin: 2px; border-radius: 5px; }}
        QListWidget::item:selected {{ background: #168f83; color: white; }}
        QTabWidget::pane {{ border: 1px solid {border}; border-radius: 5px; }}
        QTabBar::tab {{ padding: 9px 14px; }}
        QTabBar::tab:selected {{ color: #26b7a4; border-bottom: 2px solid #26b7a4; }}
        QProgressBar {{ border: none; background: {border}; border-radius: 3px; height: 6px; }}
        QProgressBar::chunk {{ background: #26b7a4; border-radius: 3px; }}
        QSplitter::handle {{ background: {border}; width: 1px; }}
    """)
