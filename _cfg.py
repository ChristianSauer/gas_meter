import yaml
import os
import pathlib
from loguru import logger
from dataclasses import dataclass


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


default_path = str(pathlib.Path(__file__).parent / "config.yml")

path = os.environ.get("GAS_METER_CONFIG_PATH", default_path)
logger.info("loading config from {}", path)
with open(path, "r") as yml_file:
    _data = yaml.safe_load(yml_file)
    config = Config(**_data)