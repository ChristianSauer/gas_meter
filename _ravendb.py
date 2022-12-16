import pathlib

from pyravendb.store import document_store
import datetime
from dataclasses import dataclass

import _cfg

doc_id = "data/gas"
config = _cfg.config

_store = None


@dataclass(eq=True, frozen=True)
class Data:
    readingType: str


def store_result(value: float):
    store = get_store()

    with store.open_session() as session:
        gas_doc = session.load(doc_id, object_type=Data)

        if not gas_doc:
            data = Data(readingType="gas")
            session.store(data, key=doc_id)
            session.save_changes()

        time_series = session.time_series_for(doc_id, config.ravendb_time_series_name)
        time_series.append(datetime.datetime.utcnow(), [value])
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
