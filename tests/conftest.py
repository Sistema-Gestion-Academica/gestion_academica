from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.dbbroker import DBBroker
from app.utils.mapper import Mapper


@pytest.fixture
def mapper_tmp_dir(tmp_path, monkeypatch):
    """crea un directorio temporal data para la ejecución del test, sobrescribe Mapper._DATA_DIR para que todo se guarde ahí, y reinicia el singleton DBBroker antes y después."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr(Mapper, "_DATA_DIR", data_dir, raising=False)
    DBBroker._instance = None
    yield data_dir
    DBBroker._instance = None


@pytest.fixture
def isolated_broker(mapper_tmp_dir):
    """depende de mapper_tmp_dir, instancia un DBBroker que ya usa ese almacenamiento aislado y lo entrega al test."""
    broker = DBBroker()
    yield broker
    DBBroker._instance = None
