import os
import sys

from pydicom import dcmread
from pynetdicom import AE

DCM_DIR = './dcm/'

if __name__ == '__main__':

    print('#######################')
    print('#    test_store.py    #')
    print('#######################')

    try:
        file_name = DCM_DIR + sys.argv[1]
        print('File to send: {}'.format(file_name))
        ds = dcmread(file_name)
    except FileNotFoundError:
        for f in os.listdir(DCM_DIR):
            print(f)
        sys.exit()

    ae = AE()
    storage_class = str(ds.file_meta['MediaStorageSOPClassUID'].value)
    ae.add_requested_context(storage_class)
    # ae.add_requested_context('1.2.840.10008.5.1.4.1.1.6.1')
    # [Ultrasound Image Storage]

    print(ds.file_meta)

    assoc = ae.associate('127.0.0.1', 104)
    if assoc.is_established:
        print('Sending file {} to localhost-scp-server'.format(file_name))
        status = assoc.send_c_store(ds)
        if status:
            # If the storage request succeeded this will be 0x0000
            print('C-STORE request status: 0x{0:04x}'.format(status.Status))
        else:
            print('Connection timed out, was aborted or received invalid response')
        assoc.release()
    else:
        print('Association rejected, aborted or never connected')
