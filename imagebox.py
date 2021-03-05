from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import (QGroupBox, QVBoxLayout, QLabel, QLineEdit)


class ImageBox(QGroupBox):
    # 400px - target width of image for ImageBox TODO: Get this from settings
    VIEW_IMAGE_WIDTH = 400

    def __init__(self, pixmap: QPixmap, image_info: str):
        super().__init__()

        self.image_info = image_info
        self.setTitle(image_info)

        self.setCheckable(True)
        self.setChecked(True)
        font = self.font()
        font.setPixelSize(12)
        self.setFont(font)

        self.pixmap = pixmap

        self.img = QLabel()
        ratio = self.VIEW_IMAGE_WIDTH / float(pixmap.width())
        height = int(float(pixmap.height()) * float(ratio))
        self.img.resize(self.VIEW_IMAGE_WIDTH, height)
        self.img.setPixmap(self.pixmap.scaled(self.img.size(),
                                              Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation))

        self.comment = QLineEdit(self)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.img)
        self.layout.addWidget(self.comment)
        self.setLayout(self.layout)

        self.setFixedWidth(self.contentsMargins().left() +
                           self.contentsMargins().right() +
                           self.img.width() +
                           (self.layout.spacing() * 2))
        self.setFixedHeight(self.contentsMargins().top() +
                            self.contentsMargins().bottom() +
                            self.img.height() + self.comment.height() +
                            (self.layout.spacing() * 3))

    def change(self):
        self.setChecked(not self.isChecked())
