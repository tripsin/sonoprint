import socket

from pydicom import Dataset
from pydicom.charset import python_encoding


def try_port(port: int):
    """ Return True if *port* free """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind(("0.0.0.0", port))
        result = True
    except Exception as e:
        print('Port {} is busy.'.format(port))
        print(e)
    finally:
        sock.close()
    return result


def decode_rus(s: str, dataset: Dataset):
    # исправляем кодировку на русскую
    result = bytes(s, python_encoding[str(dataset.SpecificCharacterSet)]) \
        .decode(python_encoding['ISO_IR 144'])  # fro Russian
    # если строка повторяется, то берем половину
    left = result[:len(result) // 2]
    right = result[len(result) // 2:len(result)]
    if left == right:
        result = left
    return result
