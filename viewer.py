import sys

from PySide2 import QtPrintSupport
from PySide2.QtCore import QPoint, QRect
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import (QMainWindow, QAction, QApplication, QLabel,
                               QFileDialog, QStyle, QCommonStyle, QListWidgetItem)
from pydicom import dcmread

from getusimage import get_qpxmap_from
from scp_server import SCPServer

from imagebox import ImageBox, ImageList, QListWidget


class Viewer(QMainWindow):

    def __init__(self):
        try:
            super().__init__()

            self.imagebox = ImageBox()
            self.setCentralWidget(self.imagebox)
            # self.lbl = QLabel(self)
            # self.setCentralWidget(self.lbl)

            '''
            self.viewer = QListWidget(self)
            self.setCentralWidget(self.viewer)
            self.viewer.setViewMode(QListWidget.IconMode)
            '''

            st = QCommonStyle()

            open_action = QAction(st.standardIcon(QStyle.SP_DialogOpenButton), 'Open DCM', self)
            open_action.setShortcut('Ctrl+O')
            open_action.setStatusTip('Open DCM file')
            open_action.triggered.connect(self.open_dcm_file)

            printer_action = QAction(st.standardIcon(QStyle.SP_FileDialogDetailedView), 'Print image', self)
            printer_action.triggered.connect(self.print_image)

            preview_action = QAction(st.standardIcon(QStyle.SP_FileDialogContentsView), 'Preview Print', self)
            preview_action.triggered.connect(self.preview_print)

            self.statusBar()

            menubar = self.menuBar()
            file_menu = menubar.addMenu('&File')
            file_menu.addAction(open_action)
            print_menu = menubar.addMenu('&Print')
            print_menu.addAction(printer_action)
            preview_menu = menubar.addMenu('Pre&view')
            preview_menu.addAction(preview_action)

            toolbar = self.addToolBar('Open')
            toolbar.addAction(open_action)
            printtool = self.addToolBar('Print')
            printtool.addAction(printer_action)
            previewtool = self.addToolBar('Preview')
            previewtool.addAction(preview_action)

            self.setGeometry(300, 300, 350, 250)
            self.setWindowTitle('Main window')
            self.show()

            # --------------------------
            # Init and Start SCP server
            # --------------------------

            self.current_pixmap = None
            self.scp = SCPServer(self.show_dicom_image)
            self.scp.start()

            # --------------------------

        except Exception as e:
            print(e)
            sys.exit()

    def show_dicom_image(self, ds):
        try:
            self.current_pixmap = get_qpxmap_from(ds)
            # self.lbl.setPixmap(self.current_pixmap)

            self.imagebox.set_image(self.current_pixmap)
            self.imagebox.set_title(ds.file_meta['MediaStorageSOPInstanceUID'].value)

            '''
            last_image = ImageBox()
            last_image.set_image(self.current_pixmap)
            last_image.set_title(ds.file_meta['MediaStorageSOPInstanceUID'].value)
            view_item = QListWidgetItem(self.viewer)
            # view_item.setSizeHint(last_image.sizeHint())
            view_item.setSizeHint(last_image.size())
            print(last_image.size())
            self.viewer.addItem(view_item)
            self.viewer.setItemWidget(view_item, last_image)
            # print(self.viewer.viewMode())
            '''

        except Exception as e:
            print(e)



    def open_dcm_file(self):
        try:
            fn = QFileDialog.getOpenFileName(self, 'Выбрать DICOM-файл', '', '*.dcm')[0]
            if fn:
                self.show_dicom_image(dcmread(fn))
        except Exception as e:
            print(e)

    def print_image(self):
        if self.current_pixmap:
            printer = QtPrintSupport.QPrinter()
            dialog = QtPrintSupport.QPrintDialog(printer, self)
            dialog.setWindowTitle('Print image')
            if dialog.exec_() == dialog.Accepted:
                painter = QPainter()
                painter.begin(printer)
                p = QPoint(0, 0)
                r = QRect(150, 100, 300, 300)
                painter.drawPixmap(p, self.current_pixmap, r)
                painter.end()

    def preview_print(self):
        if self.current_pixmap:
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.paintRequested.connect(self.handle_paint_request)
            dialog.exec_()

    def handle_paint_request(self, printer):
        painter = QPainter()
        painter.begin(printer)
        p = QPoint(0, 0)
        r = QRect(0, 95, 800, 760)
        painter.drawPixmap(p, self.current_pixmap, r)
        painter.end()
        # self.view.render(painter) # for components


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Viewer()
    sys.exit(app.exec_())
