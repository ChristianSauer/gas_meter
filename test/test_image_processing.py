import io
from io import BytesIO
from unittest import mock

import cv2
import numpy as np
import pytest
import pytesseract

_count = 0


def test_can_read_image():
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

    with mock.patch('imagestore.ImageStore') as MockImgStore:
        with open("000_original.jpg", "rb") as f:
            import _image_processing
            buf = BytesIO(f.read())
            result = _image_processing.ocr(buf)

        [add_image(image=x.args[0], name=x.args[1]) for x in MockImgStore.mock_calls if "add_image" in x[0]]


def add_image(image: np.ndarray, name: str):
    global _count
    is_success, buffer = cv2.imencode(".jpg", image)
    io_buf = io.BytesIO(buffer)

    counter = str(_count).zfill(3)
    with open(f"results/{counter}_{name}.jpg", "wb") as f:
        f.write(io_buf.read())
    io_buf.close()
    _count += 1
