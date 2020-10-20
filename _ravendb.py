import pathlib

from pyravendb.store import document_store
import datetime
from dataclasses import dataclass

import _cfg

config = _cfg.config

_store = None


@dataclass(eq=True, frozen=True)
class GasReading:
    reading_type: str
    value: float
    date: str


@dataclass(eq=True, frozen=True)
class DebugData:
    date: str
    Id: str


def store_result(value: float):
    reading = GasReading(reading_type="gas", value=value, date=datetime.datetime.utcnow().isoformat()[:-3]+'Z')

    store = get_store()

    with store.open_session() as session:
        session.store(reading)
        session.save_changes()


def get_store() -> document_store.DocumentStore:
    global _store

    if not _store:
        cert_path = pathlib.Path(__file__).parent / config.ravendb_pem_file

        if not cert_path.exists():
            raise FileNotFoundError(f"the cert file at {cert_path} does not exist")

        _store = document_store.DocumentStore(urls=[config.ravendb_url],
                                              database=config.ravendb_db,
                                              certificate=str(cert_path))

        _store.initialize()

    return _store
