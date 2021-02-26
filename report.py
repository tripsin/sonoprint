from PySide2.QtCore import QPoint, Qt, QRect
from PySide2.QtGui import QPainter
from PySide2.QtPrintSupport import QPrinter

from dicomimagelist import DicomImageList
from imagebox import ImageBox

# dimensions are in millimeters
MIN_ITEM_WIDTH = 80
MIN_ITEM_HEIGHT = 80
TOP_HEIGHT = 15
BOTTOM_HEIGHT = 15
LEFT_MARGIN = 20
RIGHT_MARGIN = 8
BOX_MARGINS = 2

PRINTER_DPI = 300


def mm_to_pix(mm: int):
    return int(mm * PRINTER_DPI / 25.4)


class Report:
    def __init__(self, printer: QPrinter, images: DicomImageList):
        self.printer = printer
        self.printer.setResolution(PRINTER_DPI)
        self.printer.setColorMode(QPrinter.ColorMode.GrayScale)
        self.printer.setWinPageSize(QPrinter.A4)

        self.images = images.widget_iterator()

        self.paper_width = mm_to_pix(printer.widthMM())
        self.paper_height = mm_to_pix(printer.heightMM())

        self.center_rect = QRect(mm_to_pix(LEFT_MARGIN),
                                 mm_to_pix(TOP_HEIGHT),
                                 self.paper_width - mm_to_pix(LEFT_MARGIN + RIGHT_MARGIN),
                                 self.paper_height - mm_to_pix(TOP_HEIGHT + BOTTOM_HEIGHT))

        self.columns = self.center_rect.width() // mm_to_pix(MIN_ITEM_WIDTH)
        self.rows = self.center_rect.height() // mm_to_pix(MIN_ITEM_HEIGHT)

        if (self.columns == 0) or (self.rows == 0):
            self.columns = 1
            self.rows = 1
            self.item_width = self.center_rect.width()
            self.item_height = self.center_rect.height()
        else:
            self.item_width = int(self.center_rect.width() / self.columns)
            self.item_height = int(self.center_rect.height() / self.rows)

    def _item_rect(self, top_left: QPoint):
        return QRect(top_left.x() + mm_to_pix(BOX_MARGINS),
                     top_left.y() + mm_to_pix(BOX_MARGINS),
                     self.item_width - mm_to_pix(BOX_MARGINS * 2),
                     self.item_height - mm_to_pix(BOX_MARGINS * 2))

    def make(self):

        painter = QPainter()
        painter.begin(self.printer)

        def _draw_top():
            painter.drawLine(0, mm_to_pix(TOP_HEIGHT), mm_to_pix(80), mm_to_pix(TOP_HEIGHT))
            pass

        def _draw_bottom():
            pass

        def _get_item_position():
            while True:
                _draw_top()
                _draw_bottom()
                for row in range(self.rows):
                    for column in range(self.columns):
                        x = column * self.item_width + self.center_rect.x()
                        y = row * self.item_height + self.center_rect.y()
                        yield QPoint(x, y)
                self.printer.newPage()

        def _draw_image_box(im: ImageBox, p: QPoint):
            box_rect = self._item_rect(p)
            image_rect = QRect(box_rect)
            image_rect.setHeight(image_rect.height() - 50)
            scaled_image = im.pixmap.scaled(box_rect.width(),
                                            box_rect.height(),
                                            Qt.KeepAspectRatio,
                                            Qt.SmoothTransformation)
            painter.drawPixmap(box_rect.topLeft(), scaled_image)

            painter.drawText(QPoint(p.x(),
                                    p.y() + scaled_image.height() + 50),
                             im.txt.text())

        point = _get_item_position()
        image: ImageBox
        for image in self.images:
            if image.isChecked():
                _draw_image_box(image, next(point))

        painter.end()
