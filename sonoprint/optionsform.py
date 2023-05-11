from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import (QVBoxLayout, QLabel, QSlider, QDialog)
from PySide6.QtGui import QPixmap
from PIL import ImageEnhance, ImageQt
from settings import settings, unpack_int

# loading settings:
# Spacing between ImageBoxes in ImageList
IMAGE_LIST_SPACING = int(settings.IMAGE_LIST_SPACING)

# 400px - target width of image for ImageBox
VIEW_IMAGE_WIDTH = int(settings.VIEW_IMAGE_WIDTH)

BOX_FONT_SIZE = int(settings.BOX_FONT_SIZE)

IMAGE_CROPPING_RECT = QRect(*unpack_int(settings.IMAGE_CROPPING_RECT))


class OptionsForm(QDialog):
    def __init__(self, pixmap: QPixmap):
        super().__init__()

        ratio = VIEW_IMAGE_WIDTH / float(pixmap.width())
        height = int(float(pixmap.height()) * float(ratio))

        self.img = QLabel()
        self.img.resize(VIEW_IMAGE_WIDTH, height)

        self.pixmap = pixmap.scaled(self.img.size(),
                                              Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation)
        self.tmp_pil_img = ImageQt.fromqpixmap(self.pixmap)

        #self.img.setPixmap(self.pixmap)
        #self.img.setPixmap(self.pixmap.scaled(self.img.size(),
        #                                      Qt.KeepAspectRatio,
        #                                      Qt.SmoothTransformation))

        self.sldBrightness = QSlider()
        self.sldBrightness.setMaximum(500)
        self.sldBrightness.setValue(100)
        self.sldBrightness.setOrientation(Qt.Horizontal)
        self.sldBrightness.setTickPosition(QSlider.TicksBothSides)

        self.sldContrast = QSlider()
        self.sldContrast.setMaximum(500)
        self.sldContrast.setValue(100)
        self.sldContrast.setOrientation(Qt.Horizontal)
        self.sldContrast.setTickPosition(QSlider.TicksBothSides)

        self.sldSharpness = QSlider()
        self.sldSharpness.setMaximum(400)
        self.sldSharpness.setMinimum(-100)
        self.sldSharpness.setValue(100)
        self.sldSharpness.setOrientation(Qt.Horizontal)
        self.sldSharpness.setTickPosition(QSlider.TicksBothSides)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addWidget(self.img)
        self.vertical_layout.addWidget(self.sldBrightness)
        self.vertical_layout.addWidget(self.sldContrast)
        self.vertical_layout.addWidget(self.sldSharpness)
        self.setLayout(self.vertical_layout)

        self.sldBrightness.valueChanged.connect(self.doo)
        self.sldContrast.valueChanged.connect(self.doo)
        self.sldSharpness.valueChanged.connect(self.doo)

        self.doo()

    def doo(self):
        sh = float(self.sldSharpness.value()) / 100
        br = float(self.sldBrightness.value()) / 100
        co = float(self.sldContrast.value()) / 100

        #tmp_img = ImageQt.ImageQt(self.img.pixmap().toImage())
        #tmp_img = self.tmp_pil_img

        tmp_img = ImageEnhance.Sharpness(self.tmp_pil_img).enhance(sh)

        tmp_img = ImageEnhance.Brightness(tmp_img).enhance(br)

        tmp_img = ImageEnhance.Contrast(tmp_img).enhance(co)

        self.img.setPixmap(ImageQt.toqpixmap(tmp_img))
