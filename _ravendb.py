import pathlib

from pyravendb.store import document_store
import datetime
from dataclasses import dataclass

import _cfg

config = _cfg.config


@dataclass(eq=True, frozen=True)
class GasReading:
    reading_type: str
    value: float
    date: datetime.datetime  # todo is this correctly serialized?


def store_result(value: float):

    reading = GasReading(reading_type="gas", value=value, date=datetime.datetime.utcnow())

    cert_path = pathlib.Path(__file__).parent / config.ravendb_pem_file

    if not cert_path.exists():
        raise FileNotFoundError(f"the cert file at {cert_path} does not exist")

    store = document_store.DocumentStore(urls=[config.ravendb_url],
                                         database=config.ravendb_db,
                                         certificate=str(cert_path))
    store.initialize()
    with store.open_session() as session:
        session.store(reading)
        session.save_changes()
