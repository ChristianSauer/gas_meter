import click
import RPi.GPIO as GPIO
import time
import _cfg
import _ravendb
import datetime

from loguru import logger

config = _cfg.config

@click.command()
def capture():
    logger.info("initializing")

    switch = config.gpio_bcm_nr

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(switch, GPIO.IN)

    try:
        while True:
            if GPIO.input(switch):
                _ravendb.store_result(0.01)
                logger.info("reed contact triggered")
                _delay_for_seconds(config.debounce_seconds)

            _delay_for_seconds(config.timeout_seconds)
    finally:
        GPIO.cleanup()


def _delay_for_seconds(seconds: int):
    next_run = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
    wait_time = next_run - datetime.datetime.utcnow()
    seconds = wait_time.total_seconds()
    logger.info("Waiting until {next_run} -> {seconds} seconds", next_run=next_run, seconds=seconds)

    time.sleep(seconds)


if __name__ == '__main__':
    capture()
