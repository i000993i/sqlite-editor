import os
import tempfile
import threading
import pytest

from functions.database import DatabaseManager


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    m = DatabaseManager()
    assert m.connect(str(path))
    m.connection.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
    m.connection.execute("INSERT INTO t (name) VALUES ('a'), ('b'), ('c')")
    m.connection.commit()
    yield m
    m.close()


def test_get_tables(db):
    tables = db.get_tables()
    assert len(tables) == 1
    assert tables[0][0] == "t"
    assert tables[0][1] == 3


def test_get_table_page(db):
    ok, data, cols, total, err = db.get_table_page("t", 0, 2)
    assert ok and total == 3
    assert cols[0] == "rowid"
    assert len(data) == 2


def test_update_insert_delete(db):
    ok, data, _, total, _ = db.get_table_page("t", 0, 10)
    rowid = data[0][0]

    ok, err = db.update_cell("t", "name", "z", rowid)
    assert ok, err

    ok, new_id = db.insert_row("t", [None, "d"])
    assert ok and new_id is not None

    ok, err = db.delete_row("t", rowid)
    assert ok, err


def test_invalid_names(db):
    assert not db.update_cell("t; DROP TABLE t", "name", "x", 1)[0]
    assert not db.update_cell("t", "name); --", "x", 1)[0]


def test_concurrent_reads(db):
    """Читаем из нескольких потоков одновременно — не должно быть ошибок."""
    errors = []

    def reader():
        try:
            for _ in range(20):
                ok, *_ = db.get_table_page("t", 0, 5)
                if not ok:
                    errors.append("read failed")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=reader) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors