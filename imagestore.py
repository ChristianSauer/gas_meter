import io
import uuid
from datetime import datetime, timedelta

import cv2
import numpy as np

import _ravendb


class ImageStore:
    def __init__(self, cfg):
        self._config = cfg
        self._count = 0
        self._images = []

    def __enter__(self):
        self._store = _ravendb.get_store()
        self._session = self._store.open_session(database="debug_data")

        utc_now = datetime.utcnow().isoformat()[:-3] + 'Z'

        id_ = str(uuid.uuid4()).replace("-", "")

        expires = (datetime.utcnow() + timedelta(hours=self._config.image_retaining_hours)).isoformat()[:-3] + 'Z'
        self._document = _ravendb.DebugData(utc_now, f"debug_data/gas/{id_}")
        self._session.save_entity(self._document.Id, self._document, {},
                                  {"@expires": expires, "@id": self._document.Id}, {})
        self._session.save_changes()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._session.save_changes()
        for img in self._images:
            img: io.BytesIO
            img.close()

        self._images = None

    def add_image(self, image: np.ndarray, name: str):
        is_success, buffer = cv2.imencode(".jpg", image)
        io_buf = io.BytesIO(buffer)

        counter = str(self._count).zfill(3)
        self._session.advanced.attachment.store(self._document.Id, f"{counter}_{name}.jpg", io_buf, "image/jpg")
        self._session.save_changes()
        io_buf.close()
        self._count += 1