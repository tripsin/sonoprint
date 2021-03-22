from pynetdicom import AE, VerificationPresentationContexts

if __name__ == '__main__':

    print('#######################')
    print('#     test_echo.py    #')
    print('#######################')

    ae = AE()
    ae.requested_contexts = VerificationPresentationContexts
    ae.ae_title = b'TEST_ECHO'
    # ae.add_requested_context('1.2.840.10008.1.1') # 'VerificationSOPClass'

    assoc = ae.associate('127.0.0.1', 104)
    if assoc.is_established:
        print(ae.ae_title)
        print('Sending C_ECHO to localhost-scp-server')
        status = assoc.send_c_echo()
        if status:
            # If the storage request succeeded this will be 0x0000
            print('C-ECHO request status: 0x{0:04x}'.format(status.Status))
        else:
            print('Connection timed out, was aborted or received invalid response')
        assoc.release()
    else:
        print('Association rejected, aborted or never connected')
