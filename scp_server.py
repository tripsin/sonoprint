import socket

from pynetdicom import AE, evt
from pydicom.uid import ImplicitVRLittleEndian

from getusimage import get_qpxmap_from


def try_port(port):
    """ Return True if *port* free """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind(("0.0.0.0", port))
        result = True
    except Exception as e:
        print('\nERROR: ', e)
    finally:
        sock.close()
    return result


class SCPServer:

    def __init__(self, viewer):
        self.ae = AE()
        self.ae.add_supported_context('1.2.840.10008.5.1.4.1.1.6.1',
                                      ImplicitVRLittleEndian)  # UltrasoundImageStorage
        self.handlers = [(evt.EVT_C_STORE, self.handle_c_store)]
        self.viewer = viewer
        # print('DEBUG-SCP-SERVER: viewer - ', self.viewer)

    def start(self):
        try:
            print('Server IMG starting ...\n')
            if try_port(104):
                self.ae.start_server(('', 104), block=False, evt_handlers=self.handlers)
        except Exception as e:
            print('ERROR: ', e)

    def stop(self):
        self.ae.shutdown()

    def handle_c_store(self, event):
        """ Handle EVT_C_STORE events. """
        try:
            # print('\nDEBUG: start handling C-STORE')
            self.ds = event.dataset
            self.ds.file_meta = event.file_meta
            self.viewer.setPixmap(get_qpxmap_from(self.ds))
            # print('\nDEBUG: DATESET sent to QPixmap!')
        except Exception as e:
            print('\nERROR: ', e)
            return 0xC001
        return 0x0000
