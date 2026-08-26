import pytest
import database


@pytest.fixture(autouse=True)
def test_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test_mini_amazon.db"

    monkeypatch.setattr(database, "DB_NAME", test_db)

    database.create_tables()

    yield test_db