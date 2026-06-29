import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from functions.database import DatabaseManager
from functions.logger import setup_logger
setup_logger('test', level=60)


class TestDatabaseManager:

    def setup_method(self):
        self.db = DatabaseManager()
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db.create_database(self.tmp.name)

    def teardown_method(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_connect_and_close(self):
        assert self.db.connection is not None
        assert self.db.current_db == self.tmp.name

    def test_create_table_and_get_tables(self):
        success, err = self.db.create_table("test_table", [
            {'name': 'id', 'type': 'INTEGER', 'pk': True},
            {'name': 'name', 'type': 'TEXT', 'notnull': False, 'default': ''},
        ])
        assert success is True
        tables = self.db.get_tables()
        assert len(tables) >= 1
        names = [t[0] for t in tables]
        assert "test_table" in names

    def test_insert_and_query(self):
        self.db.create_table("items", [
            {'name': 'id', 'type': 'INTEGER', 'pk': True},
            {'name': 'value', 'type': 'TEXT'},
        ])
        success, rowid = self.db.insert_row("items", [1, "hello"])
        assert success is True
        success, data, cols = self.db.execute_query("SELECT * FROM items")
        assert success is True
        assert len(data) == 1
        assert data[0][1] == "hello"

    def test_update_cell(self):
        self.db.create_table("test", [
            {'name': 'id', 'type': 'INTEGER', 'pk': True},
            {'name': 'val', 'type': 'TEXT'},
        ])
        self.db.insert_row("test", [1, "old"])
        success, err = self.db.update_cell("test", "val", "new", 1)
        assert success is True
        _, data, _ = self.db.execute_query("SELECT val FROM test WHERE rowid = 1")
        assert data[0][0] == "new"

    def test_delete_row(self):
        self.db.create_table("test", [
            {'name': 'id', 'type': 'INTEGER', 'pk': True},
            {'name': 'val', 'type': 'TEXT'},
        ])
        self.db.insert_row("test", [1, "x"])
        success, err = self.db.delete_row("test", 1)
        assert success is True
        _, data, _ = self.db.execute_query("SELECT COUNT(*) FROM test")
        assert data[0][0] == 0

    def test_add_column(self):
        self.db.create_table("test", [
            {'name': 'id', 'type': 'INTEGER'},
        ])
        success, err = self.db.add_column("test", "new_col", "TEXT")
        assert success is True
        schema = self.db.get_table_schema("test")
        assert schema is not None
        names = [c['name'] for c in schema['columns']]
        assert 'new_col' in names

    def test_drop_column(self):
        self.db.create_table("test", [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'remove_me', 'type': 'TEXT'},
        ])
        success, err = self.db.drop_column("test", "remove_me")
        assert success is True
        schema = self.db.get_table_schema("test")
        names = [c['name'] for c in schema['columns']]
        assert 'remove_me' not in names

    def test_get_table_page(self):
        self.db.create_table("test", [
            {'name': 'id', 'type': 'INTEGER'},
        ])
        for i in range(10):
            self.db.insert_row("test", [i])
        success, data, cols, total, err = self.db.get_table_page("test", offset=0, limit=5)
        assert success is True
        assert len(data) == 5
        assert total == 10

    def test_search_table(self):
        self.db.create_table("test", [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'name', 'type': 'TEXT'},
        ])
        self.db.insert_row("test", [1, "apple"])
        self.db.insert_row("test", [2, "banana"])
        success, data, cols, total, err = self.db.search_table("test", "apple")
        assert success is True
        assert total == 1
