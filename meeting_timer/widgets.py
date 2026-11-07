"""Use an ordinary item delegate so popup selection stays legible in every theme."""

from PySide6.QtWidgets import QComboBox, QListView, QStyledItemDelegate


class ComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        view = QListView(self)
        view.setItemDelegate(QStyledItemDelegate(view))
        self.setView(view)
