import sys

from PySide2 import QtPrintSupport
from PySide2.QtCore import QRect
from PySide2.QtGui import QIcon
from PySide2.QtPrintSupport import QPrinter
from PySide2.QtWidgets import (QMainWindow, QAction, QApplication,
                               QFileDialog)
from pydicom import dcmread

# noinspection PyUnresolvedReferences
import rc_icons
import report
from dicomimagelist import DicomImageList
from settings import settings, unpack_int

# loading settings
from tools import log_to_file

MAIN_FORM_RECT = QRect(*unpack_int(settings.MAIN_FORM_RECT))


class Viewer(QMainWindow):

    def __init__(self):
        try:
            super().__init__()

            self.setWindowIcon(QIcon(':/icons/sonoprint.ico'))
            self.viewer = DicomImageList()
            self.setCentralWidget(self.viewer)

            new_action = QAction(QIcon(':/icons/new.ico'),
                                  'New study', self)
            new_action.setShortcut('Ctrl+N')
            new_action.setStatusTip('New study')
            # noinspection PyUnresolvedReferences
            new_action.triggered.connect(self.new_study)

            open_action = QAction(QIcon(':/icons/open.ico'),
                                  'Open DCM files', self)
            open_action.setShortcut('Ctrl+O')
            open_action.setStatusTip('Open DCM files')
            # noinspection PyUnresolvedReferences
            open_action.triggered.connect(self.open_dcm_file)

            print_action = QAction(QIcon(':/icons/print.ico'),
                                   'Preview Print', self)
            print_action.setShortcut('Ctrl+P')
            print_action.setStatusTip('Preview Print')
            # noinspection PyUnresolvedReferences
            print_action.triggered.connect(self.preview_print)

            settings_action = QAction(QIcon(':/icons/settings.ico'),
                                      'Settings', self)
            settings_action.setStatusTip('Settings')
            # noinspection PyUnresolvedReferences
            settings_action.triggered.connect(self.show_settings)

            exit_action = QAction(QIcon(':/icons/exit.ico'),
                                  'Exit', self)
            exit_action.setStatusTip('Exit')
            # noinspection PyUnresolvedReferences
            exit_action.triggered.connect(self.close)

            self.statusBar()

            menu_bar = self.menuBar()
            file_menu = menu_bar.addMenu('&File')
            file_menu.addAction(new_action)
            file_menu.addAction(open_action)
            file_menu.addAction(print_action)
            file_menu.addAction(settings_action)
            file_menu.addAction(exit_action)

            toolbar = self.addToolBar('toolbar')
            toolbar.addAction(new_action)
            toolbar.addSeparator()
            toolbar.addAction(open_action)
            toolbar.addSeparator()
            toolbar.addAction(print_action)
            toolbar.addSeparator()
            toolbar.addAction(settings_action)

            self.setGeometry(MAIN_FORM_RECT)
            self.setWindowTitle('Sonoprint')
            self.show()

        except Exception as e:
            log_to_file(str(e))
            sys.exit(-1)

    def new_study(self):
        self.viewer.clear()

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
            log_to_file('Open_File dialog failed: {}'.format(e))
            # print(e)  # TODO msg box

    def preview_print(self):
        if any(box.isChecked() for box in self.viewer.boxes()):
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.paintRequested.connect(self.handle_paint_request)
            dialog.showMaximized()
            dialog.setWindowIcon(QIcon(':/icons/sonoprint.ico'))
            dialog.exec_()

    def show_settings(self):
        # TODO
        pass

    def handle_paint_request(self, printer: QPrinter):
        if printer:
            report.make(printer, self.viewer)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Viewer()
    sys.exit(app.exec_())
