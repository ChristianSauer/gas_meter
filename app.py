import picamera
import click
import io
import time
from gpiozero import LED
from time import sleep
from fractions import Fraction
import _image_processing
import _ravendb
import datetime
from loguru import logger


@click.command()
@click.option('--timeout', default=60, help='Seconds between images')
def capture(timeout: int):
    logger.info("initializing")

    led = LED(21)

    with picamera.PiCamera(resolution=(1024, 768), framerate=Fraction(1, 6), sensor_mode=3) as camera:
        while True:
            with io.BytesIO() as data:
                _capture_image(camera, data, led)

                data.seek(0)

                result = _image_processing.ocr(data)

                _ravendb.store_result(result)

            _delay_for_timeout_seconds(timeout)


def _delay_for_timeout_seconds(timeout):
    next_run = datetime.datetime.utcnow() + datetime.timedelta(seconds=timeout)
    wait_time = next_run - datetime.datetime.utcnow()
    time.sleep(wait_time.total_seconds())


def _capture_image(camera, data, led):
    print("capturing")
    led.on()

    camera.shutter_speed = 6000000
    camera.iso = 800
    # Give the camera a good long time to set gains and
    # measure AWB (you may wish to use fixed AWB instead)
    sleep(30)

    camera.exposure_mode = 'off'
    camera.capture(data, 'jpeg')
    led.off()

    print("image captured")


if __name__ == '__main__':
    capture()
