import sys
from datetime import datetime

from PySide2.QtCore import Signal, Qt, Slot
from PySide2.QtGui import QMouseEvent, QPixmap
from PySide2.QtWidgets import (QListWidget, QListWidgetItem, QGroupBox,
                               QLineEdit, QVBoxLayout, QLabel)
from pydicom import Dataset
from pydicom.uid import ImplicitVRLittleEndian
from pynetdicom import AE, evt
from pynetdicom.events import Event

from tools import get_pixmap_from, try_port, decode_rus

# Spacing between ImageBoxes in ImageList TODO: Get this from settings
IMAGE_LIST_SPACING = 5
DICOM_SCP_PORT = 104  # TODO: Get this from settings


class ImageBox(QGroupBox):
    # 400px - target width of image for ImageBox TODO: Get this from settings
    VIEW_IMAGE_WIDTH = 400

    def __init__(self, pixmap: QPixmap, image_info: str):
        super().__init__()

        self.image_info = image_info
        self.setTitle(image_info)

        self.setCheckable(True)
        self.setChecked(True)
        font = self.font()
        font.setPixelSize(12)
        self.setFont(font)

        self.pixmap = pixmap

        self.img = QLabel()
        ratio = self.VIEW_IMAGE_WIDTH / float(pixmap.width())
        height = int(float(pixmap.height()) * float(ratio))
        self.img.resize(self.VIEW_IMAGE_WIDTH, height)
        self.img.setPixmap(self.pixmap.scaled(self.img.size(),
                                              Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation))

        self.comment = QLineEdit(self)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.img)
        self.layout.addWidget(self.comment)
        self.setLayout(self.layout)

        self.setFixedWidth(self.contentsMargins().left() +
                           self.contentsMargins().right() +
                           self.img.width() +
                           (self.layout.spacing() * 2))
        self.setFixedHeight(self.contentsMargins().top() +
                            self.contentsMargins().bottom() +
                            self.img.height() + self.comment.height() +
                            (self.layout.spacing() * 3))

    def change(self):
        self.setChecked(not self.isChecked())


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
        self.__handlers = [(evt.EVT_C_STORE, self.handle_c_store)]
        self.ae = AE()
        self.ae.add_supported_context('1.2.840.10008.5.1.4.1.1.6.1',
                                      ImplicitVRLittleEndian)
        if try_port(104):
            self.ae.start_server(('', DICOM_SCP_PORT), block=False,
                                 evt_handlers=self.__handlers)
        else:
            sys.exit()
        # --------------------------

    def handle_c_store(self, event: Event) -> int:
        """
        Handle EVT_C_STORE events.
        https://ru.wikipedia.org/wiki/DICOM
        """
        try:
            ds = event.dataset
            ds.file_meta = event.file_meta
            # noinspection PyUnresolvedReferences
            self.store_signal.emit(ds)
        except Exception as e:
            print('\nERROR: ', e)
            return 0xC001
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
        box = ImageBox(get_pixmap_from(ds).copy(0, 100, 840, 668),
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
