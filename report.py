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


def make(printer: QPrinter, viewer: DicomImageList):
    printer.setResolution(PRINTER_DPI)
    printer.setColorMode(QPrinter.ColorMode.GrayScale)
    printer.setWinPageSize(QPrinter.A4)

    images = viewer.widget_iterator()

    painter = QPainter()

    # --------------------------- grid calculating ----------------------------
    paper_width = mm_to_pix(printer.widthMM())
    paper_height = mm_to_pix(printer.heightMM())

    center_rect = QRect(mm_to_pix(LEFT_MARGIN),
                        mm_to_pix(TOP_HEIGHT),
                        paper_width - mm_to_pix(LEFT_MARGIN + RIGHT_MARGIN),
                        paper_height - mm_to_pix(TOP_HEIGHT + BOTTOM_HEIGHT))

    columns = center_rect.width() // mm_to_pix(MIN_ITEM_WIDTH)
    rows = center_rect.height() // mm_to_pix(MIN_ITEM_HEIGHT)

    if (columns == 0) or (rows == 0):
        columns = 1
        rows = 1
        item_width = center_rect.width()
        item_height = center_rect.height()
    else:
        item_width = int(center_rect.width() / columns)
        item_height = int(center_rect.height() / rows)
    # ------------------------- end (grid calculating) ------------------------

    def _draw_top():
        painter.drawLine(center_rect.left(),
                         center_rect.top() - mm_to_pix(1),
                         center_rect.right(),
                         center_rect.top() - mm_to_pix(1))

    def _draw_bottom():
        painter.drawLine(center_rect.left(),
                         center_rect.bottom() + mm_to_pix(1),
                         center_rect.right(),
                         center_rect.bottom() + mm_to_pix(1))

        target_rect = QRect(QPoint(center_rect.left(),
                                   center_rect.bottom() + mm_to_pix(2)),
                            QSize(center_rect.width(),
                                  mm_to_pix(BOTTOM_HEIGHT)))

        painter.setFont(QFont('Courier', 10))
        painter.drawText(target_rect, Qt.AlignRight | Qt.AlignTop,
                         viewer.device_info)

    def _draw_image_box(box: ImageBox, p: QPoint):
        box_rect = QRect(p.x() + mm_to_pix(BOX_MARGINS),
                         p.y() + mm_to_pix(BOX_MARGINS),
                         item_width - mm_to_pix(BOX_MARGINS * 2),
                         item_height - mm_to_pix(BOX_MARGINS * 2))
        # -------------------------- header printing --------------------------
        header_rect = QRect(box_rect.left(),
                            box_rect.top(),
                            box_rect.width(), 1)

        painter.setFont(QFont('Courier', 10))
        br = painter.boundingRect(header_rect,
                                  Qt.AlignLeft | Qt.AlignBottom,
                                  box.image_info)
        header_rect.setHeight(br.height())
        painter.drawText(header_rect,
                         Qt.AlignLeft | Qt.AlignBottom,
                         box.image_info)
        # -------------------------- image printing ---------------------------
        scaled_image = box.pixmap.scaled(box_rect.width(),
                                         box_rect.height(),
                                         Qt.KeepAspectRatio,
                                         Qt.SmoothTransformation)
        image_rect = QRect(box_rect.left(),
                           box_rect.top() + header_rect.height() + 1,
                           box_rect.width(),
                           scaled_image.height())
        painter.drawPixmap(image_rect, scaled_image)
        # -------------------------- comment printing -------------------------
        comment_rect = QRect(box_rect.left(),
                             image_rect.top() + image_rect.height() + 1,
                             box_rect.width(),
                             box_rect.bottom() - image_rect.bottom())
        painter.setFont(QFont('Arial', 12))
        br = painter.boundingRect(comment_rect,
                                  Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                                  box.comment.text())
        comment_rect.setHeight(br.height())
        painter.drawText(comment_rect,
                         Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                         box.comment.text())

    def _page_engine():
        while True:
            _draw_top()
            _draw_bottom()
            for row in range(rows):
                for column in range(columns):
                    x = column * item_width + center_rect.x()
                    y = row * item_height + center_rect.y()
                    yield QPoint(x, y)
            printer.newPage()

    painter.begin(printer)
    point = _page_engine()
    image: ImageBox
    for image in images:
        if image.isChecked():
            _draw_image_box(image, next(point))
    painter.end()
