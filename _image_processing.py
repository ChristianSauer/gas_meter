import io
import pathlib
from datetime import datetime
from typing import List

import cv2
import numpy as np
import pytesseract
from loguru import logger
import _cfg

_debug = True
_timestamp = datetime.utcnow().strftime("%Y_%m_%d-%H_%M_%S")
_config = _cfg.config


def _rotate(rotation_degrees: float, image: np.ndarray) -> np.ndarray:
    point = (image.shape[1] / 2, image.shape[0] / 2)
    m = cv2.getRotationMatrix2D(point, rotation_degrees, 1)
    rotated = cv2.warpAffine(image, m, image.shape)
    # todo this cuts of part of the image, but not import right now
    return rotated


def _get_edged(image: np.ndarray) -> np.ndarray:
    edged = cv2.Canny(image, _config.canny_threshold1, _config.canny_threshold2, 1)
    return edged


def _write_disk(image: np.ndarray, name: str):
    # todo remove older folders
    # todo respect debug
    folder = pathlib.Path(__file__).parent / f"debug/{_timestamp}"
    folder.mkdir(exist_ok=True, parents=True)

    file_name = folder / f"{name}.jpg"

    ret = cv2.imwrite(str(file_name), image)

    if not ret:
        raise Exception(f"could not save file to '{file_name}'")


def find_contours(edged):
    contours, _ = cv2.findContours(edged.copy(),
                                   cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_NONE)
    dummy = edged.copy()

    bounding_boxes = []
    filtered_contours = []
    for contour in contours:
        bounds = cv2.boundingRect(contour)
        x, y, w, h = bounds

        is_tall_enough = h > 20
        is_small_enough = h < 90

        is_broad_enough = w > 5

        is_taller_than_width = w < h

        if not all([is_tall_enough,
                    is_small_enough,
                    is_broad_enough,
                    is_taller_than_width]):
            continue

        bounding_boxes.append(bounds)
        filtered_contours.append(contour)

        cv2.rectangle(dummy, (x, y), (x + w, y + h), (255, 0, 255), 2)

    _write_disk(dummy, "3_contours")
    return bounding_boxes, filtered_contours


def find_aligned_bounding_boxes(bounding_boxes):

    aligned_bounding_boxes = []
    for bb in bounding_boxes:
        tmp = find_aligned_boxes(bb, bounding_boxes)
        if len(tmp) > len(aligned_bounding_boxes):
            aligned_bounding_boxes = tmp  # todo make code more pythonic

    return aligned_bounding_boxes


def find_aligned_boxes(bb, bounding_boxes):
    result = [bb]
    for candidate in bounding_boxes[1:]:
        x1, y1, w1, h1 = bb
        x2, y2, w2, h2 = candidate
        same_y = abs(y1 - y2) < _config.bounding_box_same_y_threshold
        same_h = abs(h1 - h2) < _config.bounding_box_same_height_threshold

        if same_y and same_h:
            result.append(candidate)

    return result


def sort_bounding_boxes_left_to_right(aligned_bb):
    return sorted(aligned_bb, key=lambda x: x[0])


def image_to_text(image, sorted_aligned_bb) -> List[str]:
    result = []

    for i, bb in enumerate(sorted_aligned_bb):
        x, y, w, h = bb
        im = image[y - 5:y + h + 5, x - 5:x + w + 5]

        im = cv2.bitwise_not(im)

        _, im = cv2.threshold(im, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)  # black/white

        x = pytesseract.image_to_string(im,
                                        lang='eng',
                                        config='--psm 13 --oem 3 -c tessedit_char_whitelist=0123456789', )
        nice = x.strip()
        print(f"image number {i} recognized as '{nice}'")

        result.append(x)
    return result


def ocr_result_to_value(text: List[str]) -> float:
    cleaned = [x.strip() for x in text]
    # assert len(cleaned) == 7, "number of recognized digits is not 7"  # todo better check

    result = f'{"".join(cleaned[:5])}.{"".join(cleaned[5:])}' # number should look like "12345.23" -
    # we ignore the third fraction because its always changing when the gas meter is in operation
    return float(result)


def ocr(input_: io.BytesIO) -> float:
    input_.seek(0)

    global _timestamp
    _timestamp = datetime.utcnow().strftime("%Y_%m_%d-%H_%M_%S")

    image = cv2.imdecode(np.fromstring(input_.read(), np.uint8), 1)
    _write_disk(image, "00_original")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _write_disk(gray, "0_gray")  # todo with and use counter
    del image

    rotated = _rotate(_config.image_rotation, gray)
    _write_disk(rotated, "1_rotated")
    del gray

    edged = _get_edged(rotated)
    cv2.rectangle(edged, (0, 0), (1024, 450), (0, 0, 0), -2)  # upper crap # todo config?
    cv2.rectangle(edged, (750, 400), (1000, 600), (0, 0, 0), -2)  # last digit and m3
    _write_disk(edged, "2_edged")

    bounding_boxes, filtered_contours = find_contours(edged)

    sorted_aligned_bb = identify_likely_gas_numbers(bounding_boxes, edged)
    del edged

    numbers_as_text = image_to_text(rotated, sorted_aligned_bb)
    del rotated

    final_result = ocr_result_to_value(numbers_as_text)

    logger.info("the detected result is: {final_result}", final_result=final_result)

    return final_result

    # todo throw error if n bb < 5 and think about fractions?


def identify_likely_gas_numbers(bounding_boxes, edged):
    aligned_bb = find_aligned_bounding_boxes(bounding_boxes)
    dummy = edged.copy()  # todo function
    for bb in aligned_bb:
        x, y, w, h = bb
        cv2.rectangle(dummy, (x, y), (x + w, y + h), (255, 0, 255), 2)
    _write_disk(dummy, "5_aligned_contours")
    sorted_aligned_bb = sort_bounding_boxes_left_to_right(aligned_bb)
    return sorted_aligned_bb
