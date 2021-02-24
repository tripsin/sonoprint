import sys

from PySide2.QtCore import Signal, Qt, Slot
from PySide2.QtWidgets import QListWidget, QListWidgetItem
from pydicom import Dataset
from pydicom.uid import ImplicitVRLittleEndian
from pynetdicom import AE, evt
from pynetdicom.events import Event

from getusimage import get_qpxmap_from
from imagebox import ImageBox
from tools import try_port

# Spacing between ImageBoxes in ImageList TODO: Get this from settings
IMAGE_LIST_SPACING = 5


class DicomImageList(QListWidget):
    store_signal = Signal(Dataset)

    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSpacing(IMAGE_LIST_SPACING)
        self.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)

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
            self.ae.start_server(('', 104), block=False, evt_handlers=self.__handlers)
        else:
            sys.exit()
        # --------------------------

    def handle_c_store(self, event: Event):
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

    @Slot(Dataset)
    def store_signal_handler(self, ds: Dataset):
        box = ImageBox(get_qpxmap_from(ds), ds)
        view_item = QListWidgetItem(self)
        view_item.setSizeHint(box.size())
        self.addItem(view_item)
        self.setItemWidget(view_item, box)

    def resizeEvent(self, event):
        # TODO: Awful decision. Refresh if window resized
        self.takeItem(self.row(QListWidgetItem(self)))

    def box_list(self):
        return [self.itemWidget(self.item(i)) for i in range(self.count())]
