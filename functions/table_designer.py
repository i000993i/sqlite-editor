from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QComboBox, QTreeWidget, QTreeWidgetItem, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog,
    QInputDialog, QMessageBox, QMenu,
)
from PyQt6.QtCore import Qt
from functions.logger import models_logger
from functions.utils import validate_table_name, validate_column_name

COLUMN_TYPES = ["INTEGER", "TEXT", "REAL", "BLOB", "BOOLEAN", "DATE",
                "DATETIME", "VARCHAR(255)", "FLOAT"]

ROWID_ROLE = Qt.ItemDataRole.UserRole + 1


class ColumnTypeDialog(QDialog):
    def __init__(self, current_type="TEXT", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Тип колонки")
        self.setFixedSize(300, 120)
        self.setStyleSheet("QDialog{background:#1e1e1e;}"
                           "QLabel{color:#e0e0e0;font-size:13px;}")
        layout = QVBoxLayout(self)
        self.type_combo = QComboBox()
        self.type_combo.addItems(COLUMN_TYPES)
        self.type_combo.setCurrentText(current_type)
        self.type_combo.setStyleSheet(
            "QComboBox{background:#1a1a1a;color:#e0e0e0;border:1px solid #303030;"
            "border-radius:4px;padding:6px;font-size:14px;}"
            "QComboBox QAbstractItemView{background:#1a1a1a;color:#e0e0e0;"
            "border:1px solid #303030;}")
        layout.addWidget(QLabel("Выберите тип данных:"))
        layout.addWidget(self.type_combo)
        btns = QHBoxLayout()
        ok = QPushButton("OK")
        ok.setStyleSheet("QPushButton{background:#408040;color:white;border:none;"
                         "border-radius:4px;padding:6px 16px;}"
                         "QPushButton:hover{background:#50a050;}")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Отмена")
        cancel.setStyleSheet("QPushButton{background:#404040;color:#e0e0e0;"
                             "border:none;border-radius:4px;padding:6px 16px;}"
                             "QPushButton:hover{background:#505050;}")
        cancel.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(ok); btns.addWidget(cancel)
        layout.addLayout(btns)

    def get_type(self):
        return self.type_combo.currentText()


class TableDesigner(QWidget):

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_table = None
        self._original_columns: list[str] = []
        self._original_rowids: set[int] = set()
        self._new_col_types: dict[str, str] = {}
        self.init_ui()

    # ---------------- UI ----------------

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.table_selector = QComboBox()
        self.table_selector.setMinimumWidth(200)
        self.table_selector.setStyleSheet(
            "QComboBox{background:#1a1a1a;color:#e0e0e0;border:1px solid #303030;"
            "border-radius:4px;padding:5px 10px;font-size:13px;min-height:24px;}"
            "QComboBox QAbstractItemView{background:#1a1a1a;color:#e0e0e0;"
            "border:1px solid #303030;selection-background-color:#303030;}")
        self.table_selector.currentIndexChanged.connect(self.on_table_selected)
        toolbar.addWidget(QLabel("Таблица:"))
        toolbar.addWidget(self.table_selector)

        toolbar.addWidget(self._sep())

        for text, tip, slot in (
            ("📄 Новая", "Создать новую таблицу", self.new_table),
            ("➕ Строка", "Добавить строку", self.add_row),
            ("➖ Строка", "Удалить выбранные строки", self.delete_row),
        ):
            b = self._tool_btn(text, tip); b.clicked.connect(slot)
            toolbar.addWidget(b)

        toolbar.addWidget(self._sep())

        for text, tip, slot in (
            ("➕ Колонка", "Добавить колонку", self.add_column),
            ("➖ Колонка", "Удалить колонку", self.delete_column),
        ):
            b = self._tool_btn(text, tip); b.clicked.connect(slot)
            toolbar.addWidget(b)

        toolbar.addStretch()
        save = self._tool_btn("💾 Сохранить", "Сохранить изменения в БД", primary=True)
        save.clicked.connect(self.save_data)
        toolbar.addWidget(save)

        layout.addLayout(toolbar)

        self.grid = QTableWidget(10, 3)
        self.grid.setHorizontalHeaderLabels(["A", "B", "C"])
        self.grid.setStyleSheet("""
            QTableWidget { background:#1a1a1a; color:#e0e0e0;
                border:1px solid #303030; border-radius:3px;
                gridline-color:#282828; font-size:13px;
                alternate-background-color:#1e1e1e; }
            QTableWidget::item { padding:4px 8px; }
            QTableWidget::item:selected { background:#2a4060; color:#fff; }
            QHeaderView::section { background:#202020; color:#c0c0c0;
                border:1px solid #303030; padding:5px 8px;
                font-weight:bold; font-size:12px; }
            QHeaderView::section:horizontal { border-bottom:2px solid #408040; }
        """)
        self.grid.setAlternatingRowColors(True)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.grid.verticalHeader().setDefaultSectionSize(28)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.show_grid_context_menu)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.grid)

        info = QWidget()
        il = QHBoxLayout(info); il.setContentsMargins(0, 0, 0, 0)
        self.schema_info = QTreeWidget()
        self.schema_info.setHeaderLabels(["Свойство", "Значение"])
        self.schema_info.setMaximumHeight(120)
        self.schema_info.setStyleSheet(
            "QTreeWidget{background:#151515;color:#c0c0c0;"
            "border:1px solid #303030;border-radius:3px;font-size:12px;}"
            "QHeaderView::section{background:#202020;color:#c0c0c0;"
            "border:1px solid #303030;padding:3px 6px;font-weight:bold;}")
        il.addWidget(self.schema_info, 2)

        self.relations_widget = QTreeWidget()
        self.relations_widget.setHeaderLabels(["Таблица", "Связи"])
        self.relations_widget.setMaximumHeight(120)
        self.relations_widget.setStyleSheet(self.schema_info.styleSheet())
        il.addWidget(self.relations_widget, 3)

        splitter.addWidget(info)
        layout.addWidget(splitter)

    def _tool_btn(self, text, tip, primary=False):
        b = QPushButton(text)
        b.setToolTip(tip)
        color = "#408040" if primary else "#404040"
        hover = "#50a050" if primary else "#505050"
        b.setStyleSheet(
            f"QPushButton{{background:{color};color:white;border:none;"
            f"border-radius:4px;padding:5px 12px;font-size:12px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{hover};}}"
            f"QPushButton:disabled{{background:#2a2a2a;color:#606060;}}")
        return b

    def _sep(self):
        s = QFrame(); s.setFrameShape(QFrame.Shape.VLine)
        s.setStyleSheet("color:#303030;")
        return s

    # ---------------- connection ----------------

    def set_connection(self, db_manager):
        self.db_manager = db_manager
        self.refresh_table_list()
        self.refresh_relations()

    def refresh_table_list(self):
        self.table_selector.blockSignals(True)
        self.table_selector.clear()
        self.table_selector.addItem("— Новая таблица —", None)
        if self.db_manager and self.db_manager.connection:
            try:
                cur = self.db_manager.connection.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                for (name,) in cur.fetchall():
                    if validate_table_name(name):
                        self.table_selector.addItem(name, name)
            except Exception as e:
                models_logger.error(f"Ошибка списка таблиц: {e}")
        self.table_selector.blockSignals(False)

    def on_table_selected(self, _index):
        name = self.table_selector.currentData()
        if name:
            self.load_table(name)
        else:
            self._reset_grid()

    def _reset_grid(self):
        self.current_table = None
        self._original_columns = []
        self._original_rowids = set()
        self._new_col_types = {}
        self.grid.blockSignals(True)
        self.grid.setColumnCount(3)
        self.grid.setRowCount(10)
        self.grid.setHorizontalHeaderLabels(["A", "B", "C"])
        self.grid.blockSignals(False)
        self.schema_info.clear()

    # ---------------- load ----------------

    def load_table(self, table_name):
        if not self.db_manager or not self.db_manager.connection:
            return
        self.current_table = table_name
        try:
            cur = self.db_manager.connection.cursor()
            # rowid нужен для diff-обновления
            cur.execute(f'SELECT rowid, * FROM "{table_name}" LIMIT 1000')
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description][1:]  # без rowid

            self.grid.blockSignals(True)
            self.grid.setColumnCount(len(columns))
            self.grid.setHorizontalHeaderLabels(columns)
            self.grid.setRowCount(len(rows))

            self._original_columns = list(columns)
            self._original_rowids = set()
            self._new_col_types = {}

            for r, row in enumerate(rows):
                rowid = row[0]
                self._original_rowids.add(rowid)
                for c, val in enumerate(row[1:]):
                    item = QTableWidgetItem("" if val is None else str(val))
                    item.setData(ROWID_ROLE, rowid)
                    self.grid.setItem(r, c, item)

            self.grid.blockSignals(False)
            self.load_schema_info(table_name)
            models_logger.info(f"TableDesigner: {table_name} — {len(rows)} строк, "
                               f"{len(columns)} колонок")
        except Exception as e:
            models_logger.error(f"TableDesigner load: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить:\n{e}")

    def load_schema_info(self, table_name):
        self.schema_info.clear()
        if not self.db_manager or not self.db_manager.connection:
            return
        try:
            cur = self.db_manager.connection.cursor()
            cur.execute(f'PRAGMA table_info("{table_name}")')
            cols = cur.fetchall()
            root = QTreeWidgetItem(self.schema_info,
                                    [f"Таблица: {table_name}", f"{len(cols)} колонок"])
            root.setExpanded(True)
            for c in cols:
                flags = []
                if c[5]: flags.append("PK")
                if c[3]: flags.append("NN")
                info = c[2] or "TEXT"
                if c[4] is not None:
                    info += f" default={c[4]}"
                if flags:
                    info += f" [{','.join(flags)}]"
                QTreeWidgetItem(root, [c[1], info])
        except Exception as e:
            models_logger.error(f"schema info: {e}")

    def refresh_relations(self):
        self.relations_widget.clear()
        if not self.db_manager or not self.db_manager.connection:
            return
        try:
            cur = self.db_manager.connection.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for (name,) in cur.fetchall():
                if not validate_table_name(name):
                    continue
                cur.execute(f'PRAGMA foreign_key_list("{name}")')
                fks = cur.fetchall()
                item = QTreeWidgetItem([name, ""])
                if fks:
                    item.setText(1, "; ".join(f"{fk[3]} → {fk[2]}.{fk[4]}" for fk in fks))
                self.relations_widget.addTopLevelItem(item)
        except Exception as e:
            models_logger.error(f"relations: {e}")

    # ---------------- editing ----------------

    def new_table(self):
        self._reset_grid()
        self.table_selector.setCurrentIndex(0)

    def add_row(self):
        row = self.grid.rowCount()
        self.grid.insertRow(row)
        for c in range(self.grid.columnCount()):
            self.grid.setItem(row, c, QTableWidgetItem(""))

    def delete_row(self):
        rows = {idx.row() for idx in self.grid.selectedIndexes()}
        for r in sorted(rows, reverse=True):
            self.grid.removeRow(r)

    def add_column(self):
        dlg = ColumnTypeDialog("TEXT", self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        col = self.grid.columnCount()
        self.grid.insertColumn(col)
        label = chr(65 + col) if col < 26 else f"col{col + 1}"
        self.grid.setHorizontalHeaderItem(col, QTableWidgetItem(label))
        for r in range(self.grid.rowCount()):
            self.grid.setItem(r, col, QTableWidgetItem(""))
        self._new_col_types[label] = dlg.get_type()

    def delete_column(self):
        cols = {idx.column() for idx in self.grid.selectedIndexes()}
        for c in sorted(cols, reverse=True):
            header = self.grid.horizontalHeaderItem(c)
            if header:
                self._new_col_types.pop(header.text(), None)
            self.grid.removeColumn(c)

    def show_grid_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#1e1e1e;color:#e0e0e0;"
            "border:1px solid #303030;padding:4px;}"
            "QMenu::item{padding:6px 20px;border-radius:3px;}"
            "QMenu::item:selected{background:#303030;}"
            "QMenu::separator{height:1px;background:#303030;margin:4px 8px;}")
        col = self.grid.columnAt(pos.x())
        if col >= 0:
            act_rename = menu.addAction("✏️ Переименовать колонку")
            act_type = menu.addAction("📋 Тип колонки")
            menu.addSeparator()
            act_left = menu.addAction("⬅ Вставить колонку слева")
            act_right = menu.addAction("➡ Вставить колонку справа")
            menu.addSeparator()
            act_del = menu.addAction("❌ Удалить колонку")
        action = menu.exec(self.grid.mapToGlobal(pos))
        if col < 0 or action is None:
            return
        if action == act_rename:
            self.rename_column(col)
        elif action == act_type:
            self.change_column_type(col)
        elif action == act_del:
            self.grid.removeColumn(col)
        elif action == act_left:
            self.grid.insertColumn(col)
            self.grid.setHorizontalHeaderItem(col, QTableWidgetItem("new"))
        elif action == act_right:
            self.grid.insertColumn(col + 1)
            self.grid.setHorizontalHeaderItem(col + 1, QTableWidgetItem("new"))

    def rename_column(self, col):
        old = self.grid.horizontalHeaderItem(col)
        old_text = old.text() if old else ""
        new_text, ok = QInputDialog.getText(self, "Переименовать колонку",
                                             "Новое имя:", text=old_text)
        if ok and new_text and validate_column_name(new_text.strip()):
            self.grid.setHorizontalHeaderItem(col, QTableWidgetItem(new_text.strip()))
        elif ok and new_text:
            QMessageBox.warning(self, "Ошибка", "Некорректное имя колонки")

    def change_column_type(self, col):
        dlg = ColumnTypeDialog("TEXT", self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            header = self.grid.horizontalHeaderItem(col)
            if header:
                self._new_col_types[header.text()] = dlg.get_type()

    # ---------------- save (atomic) ----------------

    def _grid_columns(self) -> list[str]:
        return [self.grid.horizontalHeaderItem(c).text()
                if self.grid.horizontalHeaderItem(c) else f"col{c + 1}"
                for c in range(self.grid.columnCount())]

    def save_data(self):
        if not self.db_manager or not self.db_manager.connection:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте базу данных!")
            return

        table_name = self.current_table
        creating = table_name is None

        if creating:
            name, ok = QInputDialog.getText(self, "Сохранить как", "Имя новой таблицы:")
            if not ok or not name or not validate_table_name(name.strip()):
                QMessageBox.warning(self, "Ошибка", "Некорректное имя таблицы!")
                return
            table_name = name.strip()

        columns = self._grid_columns()
        if not columns or any(not validate_column_name(c) for c in columns):
            QMessageBox.warning(self, "Ошибка", "Некорректные имена колонок!")
            return

        # backup — страховка на случай ошибки в середине транзакции
        try:
            self.db_manager.backup_database()
        except Exception:
            pass

        conn = self.db_manager.connection
        cursor = conn.cursor()

        try:
            if creating:
                col_defs = []
                for c in columns:
                    col_defs.append({
                        "name": c,
                        "type": self._new_col_types.get(c, "TEXT"),
                        "pk": False, "notnull": False, "default": "",
                    })
                col_defs[0]["pk"] = True
                ok, err = self.db_manager.create_table(table_name, col_defs)
                if not ok:
                    raise RuntimeError(err)
                self.current_table = table_name
                self.refresh_table_list()
                idx = self.table_selector.findText(table_name)
                if idx >= 0:
                    self.table_selector.setCurrentIndex(idx)

            # ---- 1. добавить новые колонки ----
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            existing = {row[1] for row in cursor.fetchall()}
            for col in columns:
                if col not in existing:
                    col_type = self._new_col_types.get(col, "TEXT")
                    cursor.execute(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" {col_type}')

            # ---- 2. транзакция по данным ----
            conn.execute("BEGIN")
            try:
                # 2.1 удалить строки, которых нет в гриде
                current_rowids = set()
                for r in range(self.grid.rowCount()):
                    item = self.grid.item(r, 0)
                    if item:
                        rowid = item.data(ROWID_ROLE)
                        if rowid is not None:
                            current_rowids.add(int(rowid))
                stale = self._original_rowids - current_rowids
                for rowid in stale:
                    cursor.execute(f'DELETE FROM "{table_name}" WHERE rowid = ?',
                                    (rowid,))

                # 2.2 UPDATE существующих, INSERT новых
                for r in range(self.grid.rowCount()):
                    first = self.grid.item(r, 0)
                    rowid = first.data(ROWID_ROLE) if first else None
                    values = [
                        (self.grid.item(r, c).text() if self.grid.item(r, c) else None)
                        or None
                        for c in range(len(columns))
                    ]
                    if rowid is not None:
                        set_part = ", ".join(f'"{c}" = ?' for c in columns)
                        cursor.execute(
                            f'UPDATE "{table_name}" SET {set_part} WHERE rowid = ?',
                            values + [int(rowid)],
                        )
                    else:
                        ph = ", ".join("?" for _ in columns)
                        cols = ", ".join(f'"{c}"' for c in columns)
                        cursor.execute(
                            f'INSERT INTO "{table_name}" ({cols}) VALUES ({ph})',
                            values,
                        )

                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

            # ---- 3. обновить кэш и перезагрузить ----
            self._new_col_types = {}
            self.load_schema_info(table_name)
            self.refresh_relations()
            self.load_table(table_name)     # перечитываем с новыми rowid
            QMessageBox.information(self, "Успех", "Данные сохранены!")
            models_logger.info(f"TableDesigner сохранено: {table_name}")

        except Exception as e:
            models_logger.error(f"TableDesigner save: {e}")
            QMessageBox.critical(self, "Ошибка сохранения", str(e))