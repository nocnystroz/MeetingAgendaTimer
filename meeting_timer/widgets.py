"""Use an ordinary item delegate so popup selection stays legible in every theme."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QListView, QStyledItemDelegate

from .i18n import tr


class ComboBox(QComboBox):
    source_role = Qt.ItemDataRole.UserRole + 91
    def __init__(self, parent=None):
        super().__init__(parent)
        view = QListView(self)
        view.setItemDelegate(QStyledItemDelegate(view))
        self.setView(view)

    def addItem(self, text, userData=None):
        super().addItem(tr(text), userData)
        self.setItemData(self.count() - 1, text, self.source_role)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def retranslate_items(self):
        for index in range(self.count()):
            source = self.itemData(index, self.source_role)
            if source is not None:
                self.setItemText(index, tr(source))
