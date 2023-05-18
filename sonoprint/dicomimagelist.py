import sys
from codecs import decode
from datetime import datetime

from PySide6.QtCore import Signal, Qt, Slot, QRect
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QGroupBox,
                               QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication)
from pydicom import Dataset
from pydicom.uid import ImplicitVRLittleEndian
from pynetdicom import AE, evt
from pynetdicom.events import Event

from tools import get_pixmap_from, try_port, decode_rus, log_to_file, tune_qpixmap
from settings import settings, unpack_int
from optionsform import OptionsForm

# loading settings:
# Spacing between ImageBoxes in ImageList
IMAGE_LIST_SPACING = int(settings.IMAGE_LIST_SPACING)
# port for listening
DICOM_SCP_PORT = int(settings.DICOM_SCP_PORT)
# 400px - target width of image for ImageBox
VIEW_IMAGE_WIDTH = int(settings.VIEW_IMAGE_WIDTH)

BOX_FONT_SIZE = int(settings.BOX_FONT_SIZE)

IMAGE_CROPPING_RECT = QRect(*unpack_int(settings.IMAGE_CROPPING_RECT))


class ImageBox(QGroupBox):

    def __init__(self, pixmap: QPixmap, image_info: str):
        super().__init__()

        self.image_info = image_info
        self.setTitle(image_info)

        self.setCheckable(True)
        self.setChecked(True)
        font = self.font()
        font.setPixelSize(BOX_FONT_SIZE)
        self.setFont(font)

        self.pixmap = pixmap
        self.options = OptionsForm(self.pixmap)

        self.img = QLabel()
        ratio = VIEW_IMAGE_WIDTH / float(pixmap.width())
        height = int(float(pixmap.height()) * float(ratio))
        self.img.resize(VIEW_IMAGE_WIDTH, height)
        self.scaled_pixmap = self.pixmap.scaled(self.img.size(),
                                              Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation)
        self.draw()

        self.comment = QLineEdit(self)

        self.options_button = QPushButton('...', self)
        self.options_button.setFont(font)
        self.options_button.setFlat(True)
        self.options_button.setFixedWidth(20)

        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.comment)
        self.h_layout.addWidget(self.options_button)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addWidget(self.img)
        self.vertical_layout.addLayout(self.h_layout)
        self.setLayout(self.vertical_layout)

        self.setFixedWidth(self.contentsMargins().left() +
                           self.contentsMargins().right() +
                           self.img.width() +
                           (self.vertical_layout.spacing() * 2))
        self.setFixedHeight(self.contentsMargins().top() +
                            self.contentsMargins().bottom() +
                            self.img.height() + self.comment.height() +
                            (self.vertical_layout.spacing() * 3))

        self.options_button.clicked.connect(self.on_options_button_clicked)
        self.options.redraw.connect(self.redraw_handler)

    def change(self):
        self.setChecked(not self.isChecked())

    def draw(self):
        self.img.setPixmap(tune_qpixmap(self.scaled_pixmap,
                                        self.options.brightness(),
                                        self.options.contrast(),
                                        self.options.sharpness()))

    def on_options_button_clicked(self):
        if self.options.exec():
            self.draw()

    @Slot()
    def redraw_handler(self):
        self.draw()


class DicomImageList(QListWidget):
    store_signal = Signal(Dataset)

    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSpacing(IMAGE_LIST_SPACING)
        self.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)

        self.clinic = self.study_info = self.device_info = self.patient_id = ''

        # --------------------------
        # Init and Start SCP server
        # UltrasoundImageStorage - 1.2.840.10008.5.1.4.1.1.6.1
        # --------------------------
        # noinspection PyUnresolvedReferences
        self.store_signal.connect(self.store_signal_handler)
        self.__handlers = [(evt.EVT_C_STORE, self.handle_c_store),
                           (evt.EVT_C_ECHO, self.handle_c_echo)]
        self.ae = AE()
        self.ae.add_supported_context('1.2.840.10008.5.1.4.1.1.6.1',
                                      ImplicitVRLittleEndian)
        self.ae.add_supported_context('1.2.840.10008.1.1',
                                      ImplicitVRLittleEndian)
        if try_port(DICOM_SCP_PORT):
            self.ae.start_server(('', DICOM_SCP_PORT), block=False, ae_title=b'SONOPRINT',
                                 evt_handlers=self.__handlers)
        else:
            sys.exit(-1)
        # --------------------------

    def handle_c_store(self, event: Event) -> int:
        """
        Handle EVT_C_STORE events.
        https://ru.wikipedia.org/wiki/DICOM
        """
        print('{}: {} from {} on {} (port {})'.
              format(event.timestamp,
                     event.event.description,
                     decode(event.assoc.requestor.ae_title, 'UTF-8').strip(),
                     event.assoc.requestor.address,
                     event.assoc.requestor.port))
        try:
            ds = event.dataset
            ds.file_meta = event.file_meta
            # noinspection PyUnresolvedReferences
            self.store_signal.emit(ds)
        except Exception as e:
            log_to_file('\n HANDLE_C_STORE ERROR: {}'.format(e))
            return 0xC001
        return 0x0000

    def handle_c_echo(self, event: Event) -> int:
        print('{}: {} from {} on {} (port {})'.
              format(event.timestamp,
                     event.event.description,
                     decode(event.assoc.requestor.ae_title, 'UTF-8').strip(),
                     event.assoc.requestor.address,
                     event.assoc.requestor.port))
        return 0x0000

    def get_dicom_info(self, ds: Dataset):

        self.clinic = '{}  '. \
            format(decode_rus(ds.InstitutionName, ds))

        self.patient_id = ds.PatientID
        sd = ds.StudyDate
        st = ds.StudyTime
        dd = datetime.strptime('{} {}'.format(sd, st), '%Y%m%d %H%M%S')
        self.study_info = 'Patient ID: {}, Study time: {}'. \
            format(self.patient_id,
                   dd.strftime('%d.%m.%Y %H:%M'))

        self.device_info = 'Device: {} {} SN:{} firmware version: {}'. \
            format(ds.Manufacturer,
                   ds.ManufacturerModelName,
                   ds.DeviceSerialNumber,
                   ds.SoftwareVersions)

    @Slot(Dataset)
    def store_signal_handler(self, ds: Dataset):

        if self.patient_id != ds.PatientID:
            # new study starting
            self.clear()
            self.get_dicom_info(ds)

        ict = datetime.strptime(ds.InstanceCreationTime, '%H%M%S').time()
        box = ImageBox(get_pixmap_from(ds).copy(IMAGE_CROPPING_RECT),
                       '№{} at {}, sensor: {}, {}'
                       .format(ds.InstanceNumber,
                               ict,
                               ds.TransducerData[0],
                               decode_rus(ds.ProcessingFunction, ds)))

        view_item = QListWidgetItem(self)
        view_item.setSizeHint(box.size())
        self.addItem(view_item)
        self.setItemWidget(view_item, box)

    def resizeEvent(self, event):
        # TODO: Awful decision. Refresh if window resized
        self.takeItem(self.row(QListWidgetItem(self)))

    def boxes(self):
        for i in range(self.count()):
            yield self.itemWidget(self.item(i))

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        item = self.itemAt(event.pos())
        if item:
            self.itemWidget(item).change()
