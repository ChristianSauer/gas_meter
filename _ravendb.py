import pathlib

from pyravendb.store import document_store
import datetime
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class GasReading:
    reading_type: str
    value: float
    date: datetime.datetime  # todo is this correctly serialized?


def store_result(value: float):

    reading = GasReading(reading_type="gas", value=value, date=datetime.datetime.utcnow())

    cert_path = pathlib.Path(__file__).parent / "raven_cert/PEM/free.chsauer.client.certificate.pem"  # todo take name from config

    if not cert_path.exists():
        raise FileNotFoundError(f"the cert file at {cert_path} does not exist")

    print(str(cert_path))

    store = document_store.DocumentStore(urls=["https://a.free.chsauer.ravendb.cloud"],  # todo config!
                                         database="readings",
                                         certificate=cert_path)
    store.initialize()
    with store.open_session() as session:
        session.store(reading)
        session.save_changes()


if __name__ == '__main__':
    store_result(0.5)
