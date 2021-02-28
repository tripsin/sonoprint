import numpy
from PIL import Image
from PySide2.QtGui import QImage, QPixmap
from pydicom import dcmread


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


def _get_pil_image(dataset):
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
        ww = int(ew.value[0] if ew.VM > 1 else ew.value)
        wc = int(ec.value[0] if ec.VM > 1 else ec.value)
        image = _get_lut_value(dataset.pixel_array, ww, wc)
        # Convert mode to L since LUT has only 256 values:
        #   http://www.pythonware.com/library/pil/handbook/image.htm
        # im = PIL.Image.fromarray(image).convert('L') # Grey (from manual)
        image = Image.fromarray(image).convert('RGB')  # color

    return image


def _process(image):
    """
    Crop and calibrate image
    :type image: PIL.Image
    """

    crop_rect = (0, 95, 800, 760)  # TODO Get this from settings
    # image = image.crop(crop_rect)  # left, top, right, bottom

    # image.thumbnail(image_size, Image.LANCZOS) - damage image!
    '''
    # code for image resizing. not needed
    basewidth = width
    wpercent = (basewidth / float(image.size[0]))
    hsize = int((float(image.size[1]) * float(wpercent)))
    image = image.resize((basewidth, hsize), Image.LANCZOS)
    '''
    return image


def get_qpxmap_from(dataset):
    """ Return QT5 QPixmap from DICOM dataset"""
    image = _get_pil_image(dataset)
    image = _process(image)

    # im = im.convert('RGBA')
    # data = im.tobytes("raw","RGBA")
    # imqt = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)

    data = image.tobytes("raw", "RGB")
    qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGB888)
    return QPixmap(qim)


if __name__ == '__main__':
    im = _get_pil_image(dcmread('./test_scu/dcm/27.dcm'))
    im = _process(im)
    im.save('./27.jpg')
