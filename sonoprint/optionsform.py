from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialog, QPushButton, QApplication)
from PySide6.QtGui import QPixmap, QIcon
from PIL import ImageQt

from settings import settings
from tools import tune

# loading settings:

VIEW_IMAGE_WIDTH = int(settings.VIEW_IMAGE_WIDTH)
DEFAULT_IMAGE_BRIGHTNESS = int(settings.DEFAULT_IMAGE_BRIGHTNESS)
DEFAULT_IMAGE_CONTRAST = int(settings.DEFAULT_IMAGE_CONTRAST)
DEFAULT_IMAGE_SHARPNESS = int(settings.DEFAULT_IMAGE_SHARPNESS)


class OptionsForm(QDialog):
    redraw = Signal()

    def __init__(self, pixmap: QPixmap):
        super().__init__()

        self.saved_image_brightness = int(settings.SAVED_IMAGE_BRIGHTNESS)
        self.saved_image_contrast = int(settings.SAVED_IMAGE_CONTRAST)
        self.saved_image_sharpness = int(settings.SAVED_IMAGE_SHARPNESS)

        self.setWindowTitle('Sonoprint - Setting image characteristics')
        self.setWindowIcon(QIcon(':/icons/sonoprint.ico'))

        ratio = VIEW_IMAGE_WIDTH / float(pixmap.width())
        height = int(float(pixmap.height()) * float(ratio))

        self.img = QLabel()
        self.img.resize(VIEW_IMAGE_WIDTH, height)

        self.pixmap = pixmap.scaled(self.img.size(),
                                    Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation)
        self.tmp_pil_img = ImageQt.fromqpixmap(self.pixmap)

        self.lblBrightness = QLabel()
        self.lblBrightness.setText('Brightness')
        self.lblBrightness.setFixedWidth(60)
        self.sldBrightness = QSlider()
        self.sldBrightness.setMaximum(500)
        self.sldBrightness.setValue(self.saved_image_brightness)
        self.sldBrightness.setOrientation(Qt.Horizontal)
        self.sldBrightness.setTickPosition(QSlider.TicksBothSides)
        self.lytBrightness = QHBoxLayout()
        self.lytBrightness.addWidget(self.lblBrightness)
        self.lytBrightness.addWidget(self.sldBrightness)

        self.lblContrast = QLabel()
        self.lblContrast.setText('Contrast')
        self.lblContrast.setFixedWidth(60)
        self.sldContrast = QSlider()
        self.sldContrast.setMaximum(500)
        self.sldContrast.setValue(self.saved_image_contrast)
        self.sldContrast.setOrientation(Qt.Horizontal)
        self.sldContrast.setTickPosition(QSlider.TicksBothSides)
        self.lytContrast = QHBoxLayout()
        self.lytContrast.addWidget(self.lblContrast)
        self.lytContrast.addWidget(self.sldContrast)

        self.lblSharpness = QLabel()
        self.lblSharpness.setText('Sharpness')
        self.lblSharpness.setFixedWidth(60)
        self.sldSharpness = QSlider()
        self.sldSharpness.setMaximum(400)
        self.sldSharpness.setMinimum(-100)
        self.sldSharpness.setValue(self.saved_image_sharpness)
        self.sldSharpness.setOrientation(Qt.Horizontal)
        self.sldSharpness.setTickPosition(QSlider.TicksBothSides)
        self.lytSharpness = QHBoxLayout()
        self.lytSharpness.addWidget(self.lblSharpness)
        self.lytSharpness.addWidget(self.sldSharpness)

        self.btnReset = QPushButton('Reset')
        self.btnLoad = QPushButton('Load')
        self.btnSave = QPushButton('Save')
        self.btnApply = QPushButton('Apply')
        self.btnCancel = QPushButton('Cancel')
        self.lytButtons = QHBoxLayout()
        self.lytButtons.addWidget(self.btnReset)
        self.lytButtons.addWidget(self.btnLoad)
        self.lytButtons.addWidget(self.btnSave)
        self.lytButtons.addWidget(self.btnApply)
        self.lytButtons.addWidget(self.btnCancel)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addWidget(self.img)
        self.vertical_layout.addLayout(self.lytBrightness)
        self.vertical_layout.addLayout(self.lytContrast)
        self.vertical_layout.addLayout(self.lytSharpness)
        self.vertical_layout.addLayout(self.lytButtons)
        self.setLayout(self.vertical_layout)

        self.sldBrightness.valueChanged.connect(self.calibrate_image)
        self.sldContrast.valueChanged.connect(self.calibrate_image)
        self.sldSharpness.valueChanged.connect(self.calibrate_image)
        self.btnReset.clicked.connect(self.reset_sliders)
        self.btnLoad.clicked.connect(self.load)
        self.btnApply.clicked.connect(self.apply)
        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.cancel)

        QApplication.instance().settings_changed.connect(self.settings_changed_handler)

        self.btnApply.setDefault(True)

        self.calibrate_image()

    def calibrate_image(self):
        pixmap = tune(self.tmp_pil_img, self.sldBrightness.value(),
                      self.sldContrast.value(), self.sldSharpness.value())
        self.img.setPixmap(pixmap)

    def reset_sliders(self):
        self.sldSharpness.setValue(DEFAULT_IMAGE_SHARPNESS)
        self.sldBrightness.setValue(DEFAULT_IMAGE_BRIGHTNESS)
        self.sldContrast.setValue(DEFAULT_IMAGE_CONTRAST)

    def save(self):
        settings.save('SAVED_IMAGE_BRIGHTNESS', str(self.sldBrightness.value()))
        settings.save('SAVED_IMAGE_CONTRAST', str(self.sldContrast.value()))
        settings.save('SAVED_IMAGE_SHARPNESS', str(self.sldSharpness.value()))
        QApplication.instance().settings_changed.emit()
        self.done(1)

    def apply(self):
        self.done(1)

    def cancel(self):
        self.close()

    def load(self):
        self.sldBrightness.setValue(self.saved_image_brightness)
        self.sldContrast.setValue(self.saved_image_contrast)
        self.sldSharpness.setValue(self.saved_image_sharpness)

    def brightness(self) -> int:
        return self.sldBrightness.value()

    def contrast(self) -> int:
        return self.sldContrast.value()

    def sharpness(self) -> int:
        return self.sldSharpness.value()

    @Slot()
    def settings_changed_handler(self):
        if self.sender().parent() != self:
            self.saved_image_brightness = int(settings.SAVED_IMAGE_BRIGHTNESS)
            self.saved_image_contrast = int(settings.SAVED_IMAGE_CONTRAST)
            self.saved_image_sharpness = int(settings.SAVED_IMAGE_SHARPNESS)
            self.load()
            self.redraw.emit()
