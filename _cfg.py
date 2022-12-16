from typing import List, Dict
from typing_extensions import TypedDict

import yaml
import os
import pathlib
from loguru import logger
from dataclasses import dataclass

@dataclass()
class Config:
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

    ravendb_time_series_name: str
    "name of the timeseries, must exist"

    debounce_seconds: int
    "how many seconds to wait after a positive signal, avoids multiple countings"

    timeout_seconds: int
    "how long to wait between trying to check the switch"

    gpio_bcm_nr: int
    "the number of the GPIO pin as BCM"



default_path = str(pathlib.Path(__file__).parent / "config.yml")

path = os.environ.get("GAS_METER_CONFIG_PATH", default_path)
logger.info("loading config from {}", path)

with open(path, "r") as yml_file:
    _data = yaml.safe_load(yml_file)
    config = Config(**_data)

logger.info("config is: {config}", config=config)