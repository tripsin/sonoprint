import sys
from codecs import decode
from datetime import datetime

from PySide6.QtCore import Signal, Qt, Slot, QRect
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QListWidget, QListWidgetItem)
from pydicom import Dataset
from pydicom.uid import ImplicitVRLittleEndian
from pynetdicom import AE, evt
from pynetdicom.events import Event

from imagebox import ImageBox
from tools import get_pixmap_from, try_port, decode_rus, log_to_file
from settings import settings, unpack_int

# loading settings:
# Spacing between ImageBoxes in ImageList
IMAGE_LIST_SPACING = int(settings.IMAGE_LIST_SPACING)
# port for listening
DICOM_SCP_PORT = int(settings.DICOM_SCP_PORT)
# 400px - target width of image for ImageBox

IMAGE_CROPPING_RECT = QRect(*unpack_int(settings.IMAGE_CROPPING_RECT))


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
