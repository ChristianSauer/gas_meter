import picamera
import click
import io
import time
from gpiozero import LED
from time import sleep
from fractions import Fraction

import _cfg
import _image_processing
import _ravendb
import datetime
from loguru import logger

config = _cfg.config


@click.command()
def capture():
    logger.info("initializing")

    led = LED(config.led_gpio_number)

    with picamera.PiCamera(resolution=(1024, 768), framerate=Fraction(1, 6), sensor_mode=3) as camera:
        while True:
            with io.BytesIO() as data:
                _capture_image(camera, data, led)

                data.seek(0)

                result = _image_processing.ocr(data)

                if not result:
                    logger.warning("characters not recognized, uploading no data and trying again")
                    continue

                _ravendb.store_result(result)
                logger.info("result stored")

            _delay_for_timeout_seconds()


def _delay_for_timeout_seconds():
    next_run = datetime.datetime.utcnow() + datetime.timedelta(seconds=config.timeout)
    wait_time = next_run - datetime.datetime.utcnow()
    seconds = wait_time.total_seconds()
    logger.info("Waiting until {next_run} -> {seconds} seconds", next_run=next_run, seconds=seconds)

    time.sleep(seconds)


def _capture_image(camera, data, led):
    logger.info("capturing")
    led.on()

    camera.shutter_speed = config.shutter_speed
    camera.iso = 800
    # Give the camera a good long time to set gains and
    # measure AWB (you may wish to use fixed AWB instead)
    sleep(config.camera_wait_time)

    camera.exposure_mode = 'off'
    camera.capture(data, 'jpeg')
    led.off()

    logger.info("image captured")


if __name__ == '__main__':
    capture()
