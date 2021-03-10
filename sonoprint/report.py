from PySide2.QtCore import QPoint, Qt, QRect, QSize
from PySide2.QtGui import QPainter, QFont
from PySide2.QtPrintSupport import QPrinter

from dicomimagelist import DicomImageList, ImageBox
from settings import settings

# dimensions are in millimeters
MIN_ITEM_WIDTH = int(settings.MIN_ITEM_WIDTH)
MIN_ITEM_HEIGHT = int(settings.MIN_ITEM_HEIGHT)
TOP_HEIGHT = int(settings.TOP_HEIGHT)
BOTTOM_HEIGHT = int(settings.BOTTOM_HEIGHT)
LEFT_MARGIN = int(settings.LEFT_MARGIN)
RIGHT_MARGIN = int(settings.RIGHT_MARGIN)
BOX_MARGINS = int(settings.BOX_MARGINS)

PRINTER_DPI = int(settings.PRINTER_DPI)

TOP_CLINIC_FONT = QFont(settings.TOP_CLINIC_FONT_NAME,
                        int(settings.TOP_CLINIC_FONT_SIZE),
                        QFont.Bold)

TOP_STUDY_FONT = QFont(settings.TOP_STUDY_FONT_NAME,
                       int(settings.TOP_STUDY_FONT_SIZE))

BOTTOM_DEVICE_FONT = QFont(settings.BOTTOM_DEVICE_FONT_NAME,
                           int(settings.BOTTOM_DEVICE_FONT_SIZE))

BOX_HEADER_FONT = QFont(settings.BOX_HEADER_FONT_NAME,
                        int(settings.BOX_HEADER_FONT_SIZE))

BOX_COMMENT_FONT = QFont(settings.BOX_COMMENT_FONT_NAME,
                         int(settings.BOX_COMMENT_FONT_SIZE))


def mm_to_pix(mm: int) -> int:
    return int(mm * PRINTER_DPI / 25.4)


def make(printer: QPrinter, viewer: DicomImageList):
    printer.setResolution(PRINTER_DPI)
    printer.setColorMode(QPrinter.ColorMode.GrayScale)
    printer.setWinPageSize(QPrinter.A4)
    printer.setFullPage(True)

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
        top_rect = QRect(center_rect.left(),
                         0,
                         center_rect.width(),
                         mm_to_pix(TOP_HEIGHT - 1))
        painter.setFont(TOP_CLINIC_FONT)
        painter.drawText(top_rect, Qt.AlignRight | Qt.AlignBottom,
                         viewer.clinic)
        painter.setFont(TOP_STUDY_FONT)
        painter.drawText(top_rect, Qt.AlignLeft | Qt.AlignBottom,
                         viewer.study_info)

    def _draw_bottom():
        painter.drawLine(center_rect.left(),
                         center_rect.bottom() + mm_to_pix(1),
                         center_rect.right(),
                         center_rect.bottom() + mm_to_pix(1))

        target_rect = QRect(QPoint(center_rect.left(),
                                   center_rect.bottom() + mm_to_pix(2)),
                            QSize(center_rect.width(),
                                  mm_to_pix(BOTTOM_HEIGHT)))

        painter.setFont(BOTTOM_DEVICE_FONT)
        painter.drawText(target_rect, Qt.AlignRight | Qt.AlignTop,
                         viewer.device_info)

    def _draw_image_box(box_: ImageBox, p: QPoint):
        box_rect = QRect(p.x() + mm_to_pix(BOX_MARGINS),
                         p.y() + mm_to_pix(BOX_MARGINS),
                         item_width - mm_to_pix(BOX_MARGINS * 2),
                         item_height - mm_to_pix(BOX_MARGINS * 2))
        # -------------------------- header printing --------------------------
        header_rect = QRect(box_rect.left(),
                            box_rect.top(),
                            box_rect.width(), 1)
        painter.setFont(BOX_HEADER_FONT)
        flags = Qt.AlignLeft | Qt.AlignBottom
        br = painter.boundingRect(header_rect, flags, box_.image_info)
        header_rect.setHeight(br.height())
        painter.drawText(header_rect, flags, box_.image_info)
        # -------------------------- image printing ---------------------------
        scaled_image = box_.pixmap.scaled(box_rect.width(),
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
        painter.setFont(BOX_COMMENT_FONT)
        flags = Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap
        br = painter.boundingRect(comment_rect, flags, box_.comment.text())
        comment_rect.setHeight(br.height())
        painter.drawText(comment_rect, flags, box_.comment.text())

    def _page_engine() -> QPoint:
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
    box: ImageBox
    for box in viewer.boxes():
        if box.isChecked():
            _draw_image_box(box, next(point))
    painter.end()
