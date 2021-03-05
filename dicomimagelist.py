import sys
from datetime import datetime

from PySide2.QtCore import Signal, Qt, Slot
from PySide2.QtGui import QMouseEvent
from PySide2.QtWidgets import QListWidget, QListWidgetItem
from pydicom import Dataset
from pydicom.uid import ImplicitVRLittleEndian
from pynetdicom import AE, evt
from pynetdicom.events import Event

from tools import get_pixmap_from, try_port, decode_rus
from imagebox import ImageBox

# Spacing between ImageBoxes in ImageList TODO: Get this from settings
IMAGE_LIST_SPACING = 5
DICOM_SCP_PORT = 104  # TODO: Get this from settings


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

    def reset(self):
        # redefining a parent class function
        try:
            while self.count() > 0:
                self.removeItemWidget(self.item(0))
                self.takeItem(0)
        except AttributeError:
            pass
        super().reset()

    @Slot(Dataset)
    def store_signal_handler(self, ds: Dataset):

        if self.patient_id != ds.PatientID:
            # new study starting
            self.reset()
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

    def widget_iterator(self):
        for i in range(self.count()):
            yield self.itemWidget(self.item(i))

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        item = self.itemAt(event.pos())
        if item:
            self.itemWidget(item).change()
