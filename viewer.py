import sys

from PySide2 import QtPrintSupport
from PySide2.QtCore import QPoint
from PySide2.QtGui import QPainter
from PySide2.QtPrintSupport import QPrinter
from PySide2.QtWidgets import (QMainWindow, QAction, QApplication,
                               QFileDialog, QStyle, QCommonStyle)
from pydicom import dcmread

from dicomimagelist import DicomImageList
import report


class Viewer(QMainWindow):

    def __init__(self):
        try:
            super().__init__()

            self.viewer = DicomImageList()
            self.setCentralWidget(self.viewer)

            st = QCommonStyle()

            open_action = QAction(st.standardIcon(QStyle.SP_DialogOpenButton),
                                  'Open DCM', self)
            open_action.setShortcut('Ctrl+O')
            open_action.setStatusTip('Open DCM file')
            # noinspection PyUnresolvedReferences
            open_action.triggered.connect(self.open_dcm_file)

            printer_action = QAction(st.standardIcon(QStyle.SP_FileDialogDetailedView),
                                     'Print image', self)
            # noinspection PyUnresolvedReferences
            printer_action.triggered.connect(self.print_image)

            preview_action = QAction(st.standardIcon(QStyle.SP_FileDialogContentsView),
                                     'Preview Print', self)
            # noinspection PyUnresolvedReferences
            preview_action.triggered.connect(self.preview_print)

            self.statusBar()

            menu_bar = self.menuBar()
            file_menu = menu_bar.addMenu('&File')
            file_menu.addAction(open_action)
            print_menu = menu_bar.addMenu('&Print')
            print_menu.addAction(printer_action)
            print_menu.setDisabled(True)
            preview_menu = menu_bar.addMenu('Pre&view')
            preview_menu.addAction(preview_action)

            toolbar = self.addToolBar('Open')
            toolbar.addAction(open_action)
            print_tool = self.addToolBar('Print')
            print_tool.addAction(printer_action)
            print_tool.setDisabled(True)
            preview_tool = self.addToolBar('Preview')
            preview_tool.addAction(preview_action)

            self.setGeometry(0, 0, 900, 800)  # TODO: Get this from settings
            self.setWindowTitle('Main window')
            self.show()

        except Exception as e:
            print(e)
            sys.exit()

    def open_dcm_file(self):
        try:
            dialog = QFileDialog()
            result = dialog.getOpenFileNames(self, 'Выбрать DICOM-файлы', '',
                                             '*.dcm')
            files = result[0]
            if files:
                for fn in files:
                    self.viewer.store_signal_handler(dcmread(fn))
        except Exception as e:
            print(e)

    def print_image(self):
        if self.viewer.item(0):
            printer = QtPrintSupport.QPrinter()
            dialog = QtPrintSupport.QPrintDialog(printer, self)
            dialog.setWindowTitle('Print image')
            if dialog.exec_() == dialog.Accepted:
                self.viewer.itemWidget(self.viewer.item(0)).render(QPainter(printer),
                                                                   QPoint(0, 0))

    def preview_print(self):
        if self.viewer.item(0):
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.paintRequested.connect(self.handle_paint_request)
            dialog.showMaximized()
            dialog.exec_()

    def handle_paint_request(self, printer: QPrinter):
        if printer:
            report.make(printer, self.viewer)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Viewer()
    sys.exit(app.exec_())
