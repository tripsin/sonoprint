from PySide2.QtCore import QPoint, Qt, QRect, QSize
from PySide2.QtGui import QPainter, QFont
from PySide2.QtPrintSupport import QPrinter

from dicomimagelist import DicomImageList
from imagebox import ImageBox

# dimensions are in millimeters
MIN_ITEM_WIDTH = 80
MIN_ITEM_HEIGHT = 80
TOP_HEIGHT = 10
BOTTOM_HEIGHT = 10
LEFT_MARGIN = 10
RIGHT_MARGIN = 0
BOX_MARGINS = 2

PRINTER_DPI = 300


def mm_to_pix(mm: int):
    return int(mm * PRINTER_DPI / 25.4)


class Report:
    def __init__(self, printer: QPrinter, viewer: DicomImageList):
        self.printer = printer
        self.printer.setResolution(PRINTER_DPI)
        self.printer.setColorMode(QPrinter.ColorMode.GrayScale)
        self.printer.setWinPageSize(QPrinter.A4)

        self.viewer = viewer
        self.images = viewer.widget_iterator()

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
            painter.drawLine(self.center_rect.left(),
                             self.center_rect.top() - mm_to_pix(1),
                             self.center_rect.right(),
                             self.center_rect.top() - mm_to_pix(1))

        def _draw_bottom():
            painter.drawLine(self.center_rect.left(),
                             self.center_rect.bottom() + mm_to_pix(1),
                             self.center_rect.right(),
                             self.center_rect.bottom() + mm_to_pix(1))

            target_rect = QRect(QPoint(self.center_rect.left(),
                                       self.center_rect.bottom() + mm_to_pix(2)),
                                QSize(self.center_rect.width(),
                                      mm_to_pix(BOTTOM_HEIGHT)))

            f = QFont('Courier', 10)
            painter.setFont(f)
            br = painter.boundingRect(target_rect, Qt.AlignRight | Qt.AlignTop, self.viewer.device_info)
            if target_rect.intersected(br) != br:
                print('Out bounds!')
            painter.drawText(target_rect, Qt.AlignRight | Qt.AlignTop, self.viewer.device_info)

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

            box_rect = QRect(p.x() + mm_to_pix(BOX_MARGINS),
                             p.y() + mm_to_pix(BOX_MARGINS),
                             self.item_width - mm_to_pix(BOX_MARGINS * 2),
                             self.item_height - mm_to_pix(BOX_MARGINS * 2))

            header_rect = QRect(box_rect.left(),
                                box_rect.top(),
                                box_rect.width(), 1)

            painter.setFont(QFont('Courier', 10))
            br = painter.boundingRect(header_rect,
                                      Qt.AlignLeft | Qt.AlignBottom,
                                      im.image_info)
            header_rect.setHeight(br.height())
            painter.drawText(header_rect,
                             Qt.AlignLeft | Qt.AlignBottom,
                             im.image_info)

            scaled_image = im.pixmap.scaled(box_rect.width(),
                                            box_rect.height(),
                                            Qt.KeepAspectRatio,
                                            Qt.SmoothTransformation)
            image_rect = QRect(box_rect.left(),
                               box_rect.top() + header_rect.height() + 1,
                               box_rect.width(),
                               scaled_image.height())
            painter.drawPixmap(image_rect, scaled_image)

            comment_rect = QRect(box_rect.left(),
                                 image_rect.top() + image_rect.height() + 1,
                                 box_rect.width(),
                                 box_rect.bottom() - image_rect.bottom())
            painter.setFont(QFont('Arial', 12))
            br = painter.boundingRect(comment_rect,
                                      Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                                      im.txt.text())
            comment_rect.setHeight(br.height())
            painter.drawText(comment_rect,
                             Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                             im.txt.text())

        point = _get_item_position()
        image: ImageBox
        for image in self.images:
            if image.isChecked():
                _draw_image_box(image, next(point))

        painter.end()
