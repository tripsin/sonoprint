import PIL.Image
import numpy
from PyQt5.QtGui import QImage, QPixmap

from pydicom import dcmread

def _get_lut_value(data, window, level):
    """Apply the RGB Look-Up Table for the given
       data and window/level value."""
    return numpy.piecewise(data,
                           [data <= (level - 0.5 - (window - 1) / 2),
                            data > (level - 0.5 + (window - 1) / 2)],
                           [0, 255, lambda data: ((data - (level - 0.5)) /
                                                  (window - 1) + 0.5) * (255 - 0)])


def _get_pil_image(dataset):
    """Get Image object from Python Imaging Library(PIL)"""
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
        im = PIL.Image.frombuffer(mode, size, dataset.PixelData,
                                  "raw", mode, 0, 1)

    else:
        ew = dataset['WindowWidth']
        ec = dataset['WindowCenter']
        ww = int(ew.value[0] if ew.VM > 1 else ew.value)
        wc = int(ec.value[0] if ec.VM > 1 else ec.value)
        image = _get_lut_value(dataset.pixel_array, ww, wc)
        # Convert mode to L since LUT has only 256 values:
        #   http://www.pythonware.com/library/pil/handbook/image.htm
        #im = PIL.Image.fromarray(image).convert('L') # Grey (from manual)
        im = PIL.Image.fromarray(image).convert('RGB') # color

    return im


def _process(image):
    """Empty function. TODO: Crop and calibrate image
    :type image: PIL.Image
    """
    return image


def extract_image(dataset):
    ''' Return processed PIL.image '''
    im = _get_pil_image(dataset)
    im = _process(im)
    return im

def get_qpxmap_from(dataset):
    ''' Return QT5 QPixmap from DICOM dataset'''
    im = _get_pil_image(dataset)
    im = _process(im)
    data = im.tobytes("raw","RGB")
    qim = QImage(data, im.size[0], im.size[1], QImage.Format_RGB888)
    return QPixmap(qim)


if __name__ == '__main__':
    extract_image(dcmread('./dcm/27.dcm')).save('./img/27.jpg')
