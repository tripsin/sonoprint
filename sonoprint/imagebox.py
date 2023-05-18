from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGroupBox, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout

from optionsform import OptionsForm
from settings import settings
from tools import tune_qpixmap

VIEW_IMAGE_WIDTH = int(settings.VIEW_IMAGE_WIDTH)
BOX_FONT_SIZE = int(settings.BOX_FONT_SIZE)


class ImageBox(QGroupBox):

    def __init__(self, pixmap: QPixmap, image_info: str):
        super().__init__()

        self.image_info = image_info
        self.setTitle(image_info)

        self.setCheckable(True)
        self.setChecked(True)
        font = self.font()
        font.setPixelSize(BOX_FONT_SIZE)
        self.setFont(font)

        self.pixmap = pixmap
        self.options = OptionsForm(self.pixmap)

        self.img = QLabel()
        ratio = VIEW_IMAGE_WIDTH / float(pixmap.width())
        height = int(float(pixmap.height()) * float(ratio))
        self.img.resize(VIEW_IMAGE_WIDTH, height)
        self.scaled_pixmap = self.pixmap.scaled(self.img.size(),
                                                Qt.KeepAspectRatio,
                                                Qt.SmoothTransformation)
        self.draw()

        self.comment = QLineEdit(self)

        self.options_button = QPushButton('...', self)
        self.options_button.setFont(font)
        self.options_button.setFlat(True)
        self.options_button.setFixedWidth(20)

        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.comment)
        self.h_layout.addWidget(self.options_button)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addWidget(self.img)
        self.vertical_layout.addLayout(self.h_layout)
        self.setLayout(self.vertical_layout)

        self.setFixedWidth(self.contentsMargins().left() +
                           self.contentsMargins().right() +
                           self.img.width() +
                           (self.vertical_layout.spacing() * 2))
        self.setFixedHeight(self.contentsMargins().top() +
                            self.contentsMargins().bottom() +
                            self.img.height() + self.comment.height() +
                            (self.vertical_layout.spacing() * 3))

        self.options_button.clicked.connect(self.on_options_button_clicked)
        self.options.redraw.connect(self.redraw_handler)

    def change(self):
        self.setChecked(not self.isChecked())

    def draw(self):
        self.img.setPixmap(tune_qpixmap(self.scaled_pixmap,
                                        self.options.brightness(),
                                        self.options.contrast(),
                                        self.options.sharpness()))

    def on_options_button_clicked(self):
        if self.options.exec():
            self.draw()

    @Slot()
    def redraw_handler(self):
        self.draw()
