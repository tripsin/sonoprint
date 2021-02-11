import sys

from PySide2 import QtPrintSupport
from PySide2.QtCore import QPoint, QRect
from PySide2.QtGui import QImage, QPixmap, QIcon
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import (QMainWindow, QAction, QApplication, QLabel,
                               QFileDialog)
from pydicom import dcmread

from getusimage import extract_image
from getusimage import get_qpxmap_from
from scp_server import SCPServer


class Viewer(QMainWindow):

    def __init__(self):
        try:
            super().__init__()

            self.lbl = QLabel(self)
            self.setCentralWidget(self.lbl)

            open_action = QAction(QIcon('open.png'), 'Open DCM', self)
            open_action.setShortcut('Ctrl+O')
            open_action.setStatusTip('Open DCM file')
            open_action.triggered.connect(self.open_dcm_file)

            printer_action = QAction(QIcon('printer.png'), 'Print image', self)
            printer_action.triggered.connect(self.print_image)

            self.statusBar()

            menubar = self.menuBar()
            file_menu = menubar.addMenu('&File')
            file_menu.addAction(open_action)
            print_menu = menubar.addMenu('&Print')
            print_menu.addAction(printer_action)

            toolbar = self.addToolBar('Open')
            toolbar.addAction(open_action)
            printtool = self.addToolBar('Print')
            printtool.addAction(printer_action)

            self.setGeometry(300, 300, 350, 250)
            self.setWindowTitle('Main window')
            self.show()

            self.scp = SCPServer(self.lbl)
            self.scp.start()
        except Exception as e:
            print(e)
            sys.exit()

    def show_dicom_image(self, qt_pixel_map):
        self.lbl.setPixmap(qt_pixel_map)

    def open_dcm_file(self):
        try:
            fn = QFileDialog.getOpenFileName(self, 'Выбрать DICOM-файл', '', '*.dcm')
            im = extract_image(dcmread(fn[0]))  # PIL image

            # im = im.convert('RGBA')
            # data = im.tobytes("raw","RGBA")
            # imqt = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)

            data = im.tobytes("raw", "RGB")
            imqt = QImage(data, im.size[0], im.size[1], QImage.Format_RGB888)
            pix = QPixmap(imqt)
            self.lbl.setPixmap(pix)
        except Exception as e:
            print(e)
            sys.exit()

    def print_image(self):
        printer = QtPrintSupport.QPrinter()
        painter = QPainter()
        painter.begin(printer)
        p = QPoint(0, 0)
        r = QRect(150, 100, 300, 300)
        # TODO ds from scp_server must be refactored
        painter.drawPixmap(p, get_qpxmap_from(self.scp.ds), r)
        painter.end()

    '''
    def handlePreview(self):
        # dialog = QtPrintSupport.QPrintPreviewDialog() # PySide2
        dialog = QtGui.QPrintPreviewDialog()
        dialog.paintRequested.connect(self.handlePaintRequest)
        dialog.exec_()

    def handlePaintRequest(self, printer):
        self.view.render(QtGui.QPainter(printer))
    '''


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Viewer()
    sys.exit(app.exec_())
