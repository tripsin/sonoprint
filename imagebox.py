from PySide2.QtCore import Qt, Signal, Slot, QEvent, QModelIndex
from PySide2.QtGui import QPixmap, QTabletEvent, QShowEvent
from PySide2.QtWidgets import (QGroupBox, QVBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem)
from pydicom import Dataset

from getusimage import get_qpxmap_from

IMAGE_LIST_SPACING = 5 # Spacing between ImageBox'es in ImageList TODO: Get this from settings

class ImageList(QListWidget):
    my_signal = Signal(Dataset)

    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSpacing(IMAGE_LIST_SPACING)

        self.my_signal.connect(self.my_signal_handler)

    @Slot(Dataset)
    def my_signal_handler(self, ds):
        # 400px - target width of image for ImageBox TODO: Get this from settings
        box = ImageBox(get_qpxmap_from(ds, 400),
                       ds.file_meta['MediaStorageSOPInstanceUID'].value)
        view_item = QListWidgetItem(self)
        view_item.setSizeHint(box.size())
        self.addItem(view_item)
        self.setItemWidget(view_item, box)

    def dataset_handler(self, ds):
        self.my_signal.emit(ds)

    def resizeEvent(self, event):
        # TODO: Ugly
        self.takeItem(self.row(QListWidgetItem(self)))
        # self.currentRowChanged.emit(-1)
        # self.itemChanged.emit(self.item(0))
        # self.dataChanged(QModelIndex.row(-1), QModelIndex.row(-1)).
        # self.viewport().window().update()


class ImageBox(QGroupBox):
    """ TODO Refresh if window resized"""

    def __init__(self, pixmap: QPixmap, title):
        super().__init__()

        self.setCheckable(True)
        self.setChecked(True)
        self.setTitle(title)

        self.img = QLabel()
        self.img.resize(pixmap.size())
        self.pixmap = pixmap.scaled(self.img.size(), Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation)
        self.img.setPixmap(self.pixmap)

        self.txt = QLineEdit(self)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.img)
        self.layout.addWidget(self.txt)
        self.setLayout(self.layout)

        self.setFixedWidth(self.contentsMargins().left() +
                           self.contentsMargins().right() +
                           self.img.width() +
                           (self.layout.spacing() * 2))
        self.setFixedHeight(self.contentsMargins().top() +
                            self.contentsMargins().bottom() +
                            self.img.height() + self.txt.height() +
                            (self.layout.spacing() * 3))

    def enable(self):
        self.setChecked(True)

    def disable(self):
        self.setChecked(False)
