from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import (QGroupBox, QVBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem)
from pydicom import Dataset

from getusimage import get_qpxmap_from


class ImageList(QListWidget):
    my_signal = Signal(Dataset)

    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.my_signal.connect(self.my_signal_handler)

    def signal(self):
        return self.my_signal

    @Slot(Dataset)
    def my_signal_handler(self, ds):
        box = ImageBox(get_qpxmap_from(ds), ds.file_meta['MediaStorageSOPInstanceUID'].value)
        view_item = QListWidgetItem(self)
        view_item.setSizeHint(box.size())
        self.addItem(view_item)
        self.setItemWidget(view_item, box)

    def dataset_handler(self, ds):
        self.my_signal.emit(ds)


class ImageBox(QGroupBox):
    """ TODO Refresh if window resized"""

    def __init__(self, pixmap, title):
        super().__init__()
        self.pixmap = pixmap

        self.setCheckable(True)
        self.setChecked(True)
        self.setTitle(title)
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
