from PySide2.QtWidgets import (QGroupBox, QVBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem,
                               QAbstractScrollArea)
from PySide2.QtCore import Qt

from getusimage import get_qpxmap_from


class ImageList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def dataset_handler(self, ds):
        pixmap = get_qpxmap_from(ds)
        box = ImageBox(pixmap)
        box.set_title(ds.file_meta['MediaStorageSOPInstanceUID'].value)
        view_item = QListWidgetItem(self)
        view_item.setSizeHint(box.size())
        self.addItem(view_item)
        self.setItemWidget(view_item, box)

    def get_dataset_handler(self):
        return self.dataset_handler


class ImageBox(QGroupBox):
    """ TODO Refresh if window resized"""
    def __init__(self, pixmap):
        super().__init__()
        self.pixmap = pixmap

        self.setCheckable(True)
        self.setChecked(True)
        self.setTitle('empty')
        self.layout = QVBoxLayout(self)

        self.img = QLabel()
        self.img.setScaledContents(True)
        self.img.setPixmap(pixmap)
        self.layout.addWidget(self.img)

        self.txt = QLineEdit(self)
        self.layout.addWidget(self.txt)

        self.setLayout(self.layout)
        self.setFixedWidth(320)
        self.setFixedHeight(240)

    def enable(self):
        self.setChecked(True)

    def disable(self):
        self.setChecked(False)

    def set_title(self, name):
        self.setTitle(name)
