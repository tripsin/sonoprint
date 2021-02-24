from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import (QGroupBox, QVBoxLayout, QLabel, QLineEdit)
from pydicom import Dataset


class ImageBox(QGroupBox):
    # 400px - target width of image for ImageBox TODO: Get this from settings
    VIEW_IMAGE_WIDTH = 400

    def __init__(self, pixmap: QPixmap, ds: Dataset):
        super().__init__()

        self.setCheckable(True)
        self.setChecked(True)

        self.dataset = ds

        # noinspection PyUnresolvedReferences
        title = ('{}: ({}-{}) Датчик: {}:{}'
                 .format(str(self.dataset['InstanceNumber'].value),
                         str(self.dataset['InstanceCreationDate'].value),
                         str(self.dataset['InstanceCreationTime'].value),
                         str(self.dataset['ManufacturerModelName'].value),
                         str(self.dataset['TransducerData'].value[0])))
        self.setTitle(title)

        self.pixmap = pixmap

        self.img = QLabel()
        ratio = self.VIEW_IMAGE_WIDTH / float(pixmap.width())
        height = int(float(pixmap.height()) * float(ratio))
        self.img.resize(self.VIEW_IMAGE_WIDTH, height)
        self.img.setPixmap(self.pixmap.scaled(self.img.size(),
                                              Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation))

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
