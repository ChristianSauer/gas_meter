from typing import List, Dict
from typing_extensions import TypedDict

import yaml
import os
import pathlib
from loguru import logger
from dataclasses import dataclass


class Positions(TypedDict):
    x: int
    y: int
    w: int
    h: int


@dataclass()
class Config:
    timeout: int
    """
    Positive integer, timeout between captures in seconds
    """

    led_gpio_number: int
    """
    Number of the GPIO port
    See https://gpiozero.readthedocs.io/en/stable/recipes.html#pin-numbering for the number, e.g. GPIO17 = 17
    """

    shutter_speed: int
    """
    Positive integer, milliseconds the camera shutter stays open, e.g. 6000000
    """

    camera_wait_time: int
    """
    Time for the camera to process results etc. Default docs suggests 30 seconds
    """

    canny_threshold1: int
    """
    Threshold1 for the cv2 canny algorithm
    """

    canny_threshold2: int
    """
    Threshold2 for the cv2 canny algorithm
    """

    bounding_box_same_y_threshold: int
    """
    Bounding boxes which y axis varies less than this are considered on the same "line"
    """

    bounding_box_same_height_threshold: int
    """
    Bounding boxes which height axis varies less than this are considered to be of the same height
    """

    image_rotation: float
    """
    Degrees to rotate the image, e.g. to correct skew for me its 178
    """

    ravendb_pem_file: str
    """
    File name of the PEM for ravendb. Should be in a directory in this directory
    """

    ravendb_url: str
    """
    url of ravendb
    """

    ravendb_db: str
    "ravendb database, must exist"

    image_retaining_hours: int
    "hours to retain debug images in ravendb"

    blur_ksize_width: int
    "ksize.width for the gaussian blur kernel"

    blur_ksize_height: int
    "ksize.height for the gaussian blur kernel"

    positions: List[Dict[str, int]]
    """List of number positions. If not empty, auto detect is used"""


default_path = str(pathlib.Path(__file__).parent / "config.yml")

path = os.environ.get("GAS_METER_CONFIG_PATH", default_path)
logger.info("loading config from {}", path)

with open(path, "r") as yml_file:
    _data = yaml.safe_load(yml_file)
    config = Config(**_data)

logger.info("config is: {config}", config=config)