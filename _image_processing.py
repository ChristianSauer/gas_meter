import io
from datetime import datetime
from typing import List, Optional

import cv2
import numpy as np
import pytesseract
from loguru import logger
import _cfg
from imagestore import ImageStore

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


def find_contours(edged, img_store):
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

    img_store.add_image(dummy, "contours")
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


def image_to_text(image, sorted_aligned_bb, img_store) -> List[str]:
    result = []

    for i, bb in enumerate(sorted_aligned_bb):
        x, y, w, h = bb
        im = image[y - 5:y + h + 5, x - 5:x + w + 5]

        img_store.add_image(im, f"img_{i}")

        im = cv2.bitwise_not(im)

        _, im = cv2.threshold(im, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)  # black/white

        x = pytesseract.image_to_string(im,
                                        lang='eng',
                                        config='--psm 13 --oem 3 -c tessedit_char_whitelist=0123456789', )
        nice = x.strip()
        logger.info(f"image number {i} recognized as '{nice}'. Image position: x:{x} y:{y} w:{w} h:{h}")

        result.append(x)

    for _, bb in enumerate(sorted_aligned_bb):
        x, y, w, h = bb
        image = cv2.rectangle(image, (x-5, y-5), (x + w+5, y + h+5), (36,255,12), 1)

    img_store.add_image(image, "test")

    return result


def ocr_result_to_value(text: List[str]) -> Optional[float]:
    cleaned = [x.strip() for x in text]

    if len(cleaned) != 6:
        logger.warning(f"{''.join(cleaned)} is not of length 7 has only {len(cleaned)}")
        return None

    for txt in cleaned:
        if len(txt) == 1:
            continue

        logger.warning(f"{''.join(txt)} is not a single digit")
        return None

    result = f'{"".join(cleaned[:5])}.{"".join(cleaned[5:])}'  # number should look like "12345.23" -
    # we ignore the third fraction because its always changing when the gas meter is in operation
    return float(result)


def _use_positions():
    return [(p["x"], p["y"], p["w"], p["h"]) for p in _config.positions]


def ocr(input_: io.BytesIO) -> Optional[float]:
    input_.seek(0)

    global _timestamp
    _timestamp = datetime.utcnow().strftime("%Y_%m_%d-%H_%M_%S")
    with ImageStore(_config) as img_store:
        image = cv2.imdecode(np.fromstring(input_.read(), np.uint8), 1)
        img_store.add_image(image, "original")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        img_store.add_image(gray, "gray")
        del image

        rotated = _rotate(_config.image_rotation, gray)
        img_store.add_image(rotated, "rotated")
        del gray

        blurred = cv2.GaussianBlur(rotated, (_config.blur_ksize_width, _config.blur_ksize_height), 0)
        img_store.add_image(rotated, "blurred")
        del rotated

        edged = _get_edged(blurred)

        if _config.positions:
            logger.info("config has pre-defined positions, no auto detection")
            sorted_aligned_bb = _use_positions()
        else:
            logger.info("detecting positions of numbers automatically.")

            sorted_aligned_bb = _auto_detect_numbers(edged, img_store)

        del edged

        numbers_as_text = image_to_text(blurred, sorted_aligned_bb, img_store)
        del blurred

        final_result = ocr_result_to_value(numbers_as_text)

        logger.info("the detected result is: {final_result}", final_result=final_result)

        return final_result


def _auto_detect_numbers(edged, img_store):
    cv2.rectangle(edged, (0, 0), (1024, 450), (0, 0, 0), -2)  # upper crap # todo config?
    cv2.rectangle(edged, (750, 400), (1000, 600), (0, 0, 0), -2)  # last digit and m3
    cv2.rectangle(edged, (0, 400), (350, 600), (00, 0, 0), -2)  # before the first digit
    img_store.add_image(edged, "edged")
    bounding_boxes, filtered_contours = find_contours(edged, img_store)
    sorted_aligned_bb = identify_likely_gas_numbers(bounding_boxes, edged, img_store)
    return sorted_aligned_bb


def identify_likely_gas_numbers(bounding_boxes, edged, img_store):
    aligned_bb = find_aligned_bounding_boxes(bounding_boxes)
    dummy = edged.copy()
    img_store.add_image(dummy, "aligned_contours")
    sorted_aligned_bb = sort_bounding_boxes_left_to_right(aligned_bb)
    return sorted_aligned_bb
