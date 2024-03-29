import os
import socket

import numpy
from PIL import Image, ImageQt, ImageEnhance
from PySide6.QtGui import QImage, QPixmap
from pydicom import Dataset
from pydicom import dcmread
from pydicom.charset import python_encoding

from datetime import datetime


def _get_lut_value(data, window, level):
    """
    Apply the RGB Look-Up Table for the given
    data and window/level value.
    Magic code from pydicom example. Do not touch!
    """
    return numpy.piecewise(data,
                           [data <= (level - 0.5 - (window - 1) / 2),
                            data > (level - 0.5 + (window - 1) / 2)],
                           [0, 255, lambda data: ((data - (level - 0.5)) /
                                                  (window - 1) + 0.5) * (255 - 0)])


def _get_pil_image(dataset: Dataset) -> Image:
    """
    Get Image object from Python Imaging Library(PIL)
    Magic code from pydicom example. Do not touch!
    """
    if 'PixelData' not in dataset:
        raise TypeError("Cannot show image -- DICOM dataset does not have "
                        "pixel data")
    # can only apply LUT if these window info exists
    if ('WindowWidth' not in dataset) or ('WindowCenter' not in dataset):
        bits = dataset.BitsAllocated
        samples = dataset.SamplesPerPixel
        if bits == 8 and samples == 1:
            mode = "L"
        elif bits == 8 and samples == 3:
            mode = "RGB"
        elif bits == 16:
            # not sure about this -- PIL source says is 'experimental'
            # and no documentation. Also, should bytes swap depending
            # on endian of file and system??
            mode = "I;16"
        else:
            raise TypeError("Don't know PIL mode for %d BitsAllocated "
                            "and %d SamplesPerPixel" % (bits, samples))

        # PIL size = (width, height)
        size = (dataset.Columns, dataset.Rows)

        # Recommended to specify all details
        # by http://www.pythonware.com/library/pil/handbook/image.htm
        image = Image.frombuffer(mode, size, dataset.PixelData,
                                 "raw", mode, 0, 1)

    else:
        ew = dataset['WindowWidth']
        ec = dataset['WindowCenter']
        # noinspection PyUnresolvedReferences
        ww = int(ew.value[0] if ew.VM > 1 else ew.value)
        # noinspection PyUnresolvedReferences
        wc = int(ec.value[0] if ec.VM > 1 else ec.value)
        image = _get_lut_value(dataset.pixel_array, ww, wc)
        # Convert mode to L since LUT has only 256 values:
        #   http://www.pythonware.com/library/pil/handbook/image.htm
        # im = PIL.Image.fromarray(image).convert('L') # Grey (from manual)
        image = Image.fromarray(image).convert('RGB')  # color

    return image


def get_pixmap_from(dataset: Dataset) -> QPixmap:
    """ Return QT5 QPixmap from DICOM dataset"""
    image = _get_pil_image(dataset)
    # image = _process(image)
    data = image.tobytes("raw", "RGB")
    qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGB888)
    return QPixmap(qim)


def tune(pil_img: ImageQt, brightness, contrast, sharpness) -> QPixmap:
    sh = float(sharpness) / 100
    br = float(brightness) / 100
    co = float(contrast) / 100
    tmp_img = ImageEnhance.Sharpness(pil_img).enhance(sh)
    tmp_img = ImageEnhance.Brightness(tmp_img).enhance(br)
    tmp_img = ImageEnhance.Contrast(tmp_img).enhance(co)
    return ImageQt.toqpixmap(tmp_img)


def tune_qpixmap(pixmap: QPixmap, brightness, contrast, sharpness) -> QPixmap:
    return tune(ImageQt.fromqpixmap(pixmap), brightness, contrast, sharpness)


def try_port(port: int) -> bool:
    """ Return True if *port* free """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind(("0.0.0.0", port))
        result = True
    except Exception as e:
        log_to_file('Port {} is busy.'.format(port))
        log_to_file(e)
    finally:
        sock.close()
    return result


def decode_rus(s: str, dataset: Dataset) -> str:
    # исправляем кодировку на русскую
    result = bytes(s, python_encoding[str(dataset.SpecificCharacterSet)]) \
        .decode(python_encoding['ISO_IR 144'])  # for Russian
    # если строка повторяется, то берем половину
    left = result[:len(result) // 2]
    right = result[len(result) // 2:len(result)]
    if left == right:
        result = left
    return result


def log_to_file(message: str):
    log_path = './errors.log'
    with open(log_path, "a" if os.path.isfile(log_path) else "w") as log_file:
        log_file.write('{}: {}\n'.format(datetime.now(), message))


if __name__ == '__main__':
    im = _get_pil_image(dcmread('../test_scu/dcm/27.dcm'))
    im.save('./27.jpg')
