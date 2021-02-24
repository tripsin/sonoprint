from PySide2.QtCore import QPoint, Qt
from PySide2.QtGui import QPainter
from PySide2.QtPrintSupport import QPrinter

from imagebox import DicomImageList, ImageBox

MIN_ITEM_WIDTH = 1000
MIN_ITEM_HEIGHT = 1000


class Report:
    def __init__(self, printer: QPrinter, images: DicomImageList):
        self.printer = printer
        self.printer.setResolution(300)
        self.printer.setColorMode(QPrinter.ColorMode.GrayScale)
        self.printer.setWinPageSize(QPrinter.A4)

        self.images = images

        self.paper_width = printer.width()
        self.paper_height = printer.height()

        self.columns = self.paper_width // MIN_ITEM_WIDTH
        self.rows = self.paper_height // MIN_ITEM_HEIGHT
        self.item_width = int(self.paper_width / self.columns)
        self.item_height = int(self.paper_height / self.rows)

    def _get_item_position(self):
        while True:
            for row in range(self.rows):
                for column in range(self.columns):
                    x = column * self.item_width
                    y = row * self.item_height
                    yield QPoint(x, y)
            self.printer.newPage()

    def make(self):
        painter = QPainter()
        painter.begin(self.printer)
        point = self._get_item_position()
        image: ImageBox
        for image in self.images.box_list():
            if image.isChecked():
                new_image = image.pixmap.scaled(self.item_width - 10,
                                                self.item_height - 10,
                                                Qt.KeepAspectRatio,
                                                Qt.SmoothTransformation)
                painter.drawPixmap(next(point), new_image)
        painter.end()
