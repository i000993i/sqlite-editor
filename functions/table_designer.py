from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from functions.logger import models_logger
from functions.utils import validate_table_name, validate_column_name

COLUMN_TYPES = [
    'INTEGER', 'TEXT', 'REAL', 'BLOB', 'BOOLEAN', 'DATE', 'DATETIME', 'VARCHAR(255)', 'FLOAT'
]

class ColumnTypeDialog(QDialog):
    def __init__(self, current_type='TEXT', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Тип колонки")
        self.setFixedSize(300, 120)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; }
            QLabel { color: #e0e0e0; font-size: 13px; }
        """)
        layout = QVBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(COLUMN_TYPES)
        self.type_combo.setCurrentText(current_type)
        self.type_combo.setStyleSheet("""
            QComboBox { background-color: #1a1a1a; color: #e0e0e0;
                border: 1px solid #303030; border-radius: 4px;
                padding: 6px; font-size: 14px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a; color: #e0e0e0; border: 1px solid #303030; }
        """)
        layout.addWidget(QLabel("Выберите тип данных:"))
        layout.addWidget(self.type_combo)
        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("""
            QPushButton { background-color: #408040; color: white;
                border: none; border-radius: 4px; padding: 6px 16px; }
            QPushButton:hover { background-color: #50a050; }
        """)
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: #404040; color: #e0e0e0;
                border: none; border-radius: 4px; padding: 6px 16px; }
            QPushButton:hover { background-color: #505050; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(ok_btn); btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        self.setLayout(layout)

    def get_type(self):
        return self.type_combo.currentText()


class TableDesigner(QWidget):
    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_table = None
        self.setAcceptDrops(False)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Excel-style toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.table_selector = QComboBox()
        self.table_selector.setMinimumWidth(200)
        self.table_selector.setPlaceholderText("Выберите таблицу...")
        self.table_selector.setStyleSheet("""
            QComboBox { background-color: #1a1a1a; color: #e0e0e0;
                border: 1px solid #303030; border-radius: 4px;
                padding: 5px 10px; font-size: 13px; min-height: 24px; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow { image: none; border-left: 1px solid #303030; }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a; color: #e0e0e0;
                border: 1px solid #303030; selection-background-color: #303030; }
        """)
        self.table_selector.currentIndexChanged.connect(self.on_table_selected)
        toolbar.addWidget(QLabel("Таблица:"))
        toolbar.addWidget(self.table_selector)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #303030;")
        toolbar.addWidget(sep)

        self.new_btn = self._tool_btn("📄 Новая", "Создать новую таблицу")
        self.new_btn.clicked.connect(self.new_table)
        toolbar.addWidget(self.new_btn)

        self.add_row_btn = self._tool_btn("➕ Строка", "Добавить строку")
        self.add_row_btn.clicked.connect(self.add_row)
        toolbar.addWidget(self.add_row_btn)

        self.del_row_btn = self._tool_btn("➖ Строка", "Удалить строку(и)")
        self.del_row_btn.clicked.connect(self.delete_row)
        toolbar.addWidget(self.del_row_btn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #303030;")
        toolbar.addWidget(sep2)

        self.add_col_btn = self._tool_btn("➕ Колонка", "Добавить колонку")
        self.add_col_btn.clicked.connect(self.add_column)
        toolbar.addWidget(self.add_col_btn)

        self.del_col_btn = self._tool_btn("➖ Колонка", "Удалить колонку")
        self.del_col_btn.clicked.connect(self.delete_column)
        toolbar.addWidget(self.del_col_btn)

        toolbar.addStretch()

        self.save_btn = self._tool_btn("💾 Сохранить", "Сохранить изменения в БД", primary=True)
        self.save_btn.clicked.connect(self.save_data)
        toolbar.addWidget(self.save_btn)

        layout.addLayout(toolbar)

        self.grid = QTableWidget(10, 3)
        self.grid.setHorizontalHeaderLabels(['A', 'B', 'C'])
        self.grid.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a; color: #e0e0e0;
                border: 1px solid #303030; border-radius: 3px;
                gridline-color: #282828; font-size: 13px;
            }
            QTableWidget::item { padding: 4px 8px; }
            QTableWidget::item:selected { background-color: #2a4060; color: #ffffff; }
            QHeaderView::section {
                background-color: #202020; color: #c0c0c0;
                border: 1px solid #303030; padding: 5px 8px;
                font-weight: bold; font-size: 12px;
            }
            QHeaderView::section:horizontal { border-bottom: 2px solid #408040; }
        """)
        self.grid.setAlternatingRowColors(True)
        self.grid.setStyleSheet(self.grid.styleSheet() + """
            QTableWidget { alternate-background-color: #1e1e1e; }
        """)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.grid.verticalHeader().setDefaultSectionSize(28)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.show_grid_context_menu)

        # Bottom splitter: grid + info panel
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.grid)

        info_panel = QWidget()
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.schema_info = QTreeWidget()
        self.schema_info.setHeaderLabels(["Свойство", "Значение"])
        self.schema_info.setMaximumHeight(120)
        self.schema_info.setStyleSheet("""
            QTreeWidget { background-color: #151515; color: #c0c0c0;
                border: 1px solid #303030; border-radius: 3px; font-size: 12px; }
            QTreeWidget::item { padding: 2px 6px; }
            QHeaderView::section { background-color: #202020; color: #c0c0c0;
                border: 1px solid #303030; padding: 3px 6px; font-weight: bold; }
        """)
        info_layout.addWidget(self.schema_info, 2)

        self.relations_widget = QTreeWidget()
        self.relations_widget.setHeaderLabels(["Таблица", "Связи"])
        self.relations_widget.setMaximumHeight(120)
        self.relations_widget.setStyleSheet("""
            QTreeWidget { background-color: #151515; color: #c0c0c0;
                border: 1px solid #303030; border-radius: 3px; font-size: 12px; }
            QTreeWidget::item { padding: 2px 6px; }
            QHeaderView::section { background-color: #202020; color: #c0c0c0;
                border: 1px solid #303030; padding: 3px 6px; font-weight: bold; }
        """)
        info_layout.addWidget(self.relations_widget, 3)

        splitter.addWidget(info_panel)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def _tool_btn(self, text, tooltip, primary=False):
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        color = "#408040" if primary else "#404040"
        hover = "#50a050" if primary else "#505050"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; color: white;
                border: none; border-radius: 4px; padding: 5px 12px;
                font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:disabled {{ background-color: #2a2a2a; color: #606060; }}
        """)
        return btn

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
                cursor = self.db_manager.connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                for row in cursor.fetchall():
                    name = row[0]
                    if validate_table_name(name):
                        self.table_selector.addItem(name, name)
            except Exception as e:
                models_logger.error(f"Ошибка загрузки списка таблиц: {e}")
        self.table_selector.blockSignals(False)

    def on_table_selected(self, index):
        name = self.table_selector.currentData()
        if name:
            self.load_table(name)
        else:
            self.current_table = None
            self.grid.setColumnCount(3)
            self.grid.setRowCount(10)
            self.grid.setHorizontalHeaderLabels(['A', 'B', 'C'])
            self.schema_info.clear()
            self._new_col_types = {}

    def load_table(self, table_name):
        if not self.db_manager or not self.db_manager.connection:
            return
        self.current_table = table_name
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 1000')
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            self.grid.blockSignals(True)
            self.grid.setColumnCount(len(columns))
            self.grid.setHorizontalHeaderLabels(columns)
            self.grid.setRowCount(len(data))
            for r, row in enumerate(data):
                for c, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    self.grid.setItem(r, c, item)
            self.grid.blockSignals(False)

            self.load_schema_info(table_name)
            models_logger.info(f"Загружена таблица {table_name}: {len(data)} строк, {len(columns)} колонок")
        except Exception as e:
            models_logger.error(f"Ошибка загрузки таблицы {table_name}: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить таблицу:\n{e}")

    def load_schema_info(self, table_name):
        self.schema_info.clear()
        if not self.db_manager or not self.db_manager.connection:
            return
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            cols = cursor.fetchall()
            root = QTreeWidgetItem(self.schema_info, [f"Таблица: {table_name}", f"{len(cols)} колонок"])
            root.setExpanded(True)
            for col in cols:
                flags = []
                if col[5]: flags.append("PK")
                if col[3]: flags.append("NN")
                info = f'{col[2] or "TEXT"}'
                if col[4] is not None:
                    info += f" default={col[4]}"
                if flags:
                    info += f" [{','.join(flags)}]"
                QTreeWidgetItem(root, [col[1], info])
        except Exception as e:
            models_logger.error(f"Ошибка загрузки схемы: {e}")

    def refresh_relations(self):
        self.relations_widget.clear()
        if not self.db_manager or not self.db_manager.connection:
            return
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall() if validate_table_name(r[0])]
            for table in tables:
                item = QTreeWidgetItem([table, ""])
                cursor.execute(f'PRAGMA foreign_key_list("{table}")')
                fks = cursor.fetchall()
                if fks:
                    refs = [f"{fk[3]} → {fk[2]}.{fk[4]}" for fk in fks]
                    item.setText(1, "; ".join(refs))
                self.relations_widget.addTopLevelItem(item)
        except Exception as e:
            models_logger.error(f"Ошибка обновления связей: {e}")

    def new_table(self):
        self.current_table = None
        self.table_selector.setCurrentIndex(0)
        self.grid.setColumnCount(3)
        self.grid.setRowCount(10)
        self.grid.setHorizontalHeaderLabels(['A', 'B', 'C'])
        self.schema_info.clear()
        self._new_col_types = {}

    def add_row(self):
        row = self.grid.rowCount()
        self.grid.insertRow(row)
        for c in range(self.grid.columnCount()):
            self.grid.setItem(row, c, QTableWidgetItem(""))

    def delete_row(self):
        rows = set()
        for idx in self.grid.selectedIndexes():
            rows.add(idx.row())
        for r in sorted(rows, reverse=True):
            self.grid.removeRow(r)

    def add_column(self):
        dlg = ColumnTypeDialog('TEXT', self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            col_type = dlg.get_type()
            col = self.grid.columnCount()
            self.grid.insertColumn(col)
            label = chr(65 + col) if col < 26 else f"col{col+1}"
            self.grid.setHorizontalHeaderItem(col, QTableWidgetItem(label))
            for r in range(self.grid.rowCount()):
                self.grid.setItem(r, col, QTableWidgetItem(""))
            if not hasattr(self, '_new_col_types'):
                self._new_col_types = {}
            self._new_col_types[label] = col_type

    def delete_column(self):
        cols = set()
        for idx in self.grid.selectedIndexes():
            cols.add(idx.column())
        for c in sorted(cols, reverse=True):
            self.grid.removeColumn(c)

    def show_grid_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1e1e1e; color: #e0e0e0;
                border: 1px solid #303030; padding: 4px; }
            QMenu::item { padding: 6px 20px; border-radius: 3px; }
            QMenu::item:selected { background-color: #303030; }
            QMenu::separator { height: 1px; background: #303030; margin: 4px 8px; }
        """)

        col = self.grid.columnAt(pos.x())
        row = self.grid.rowAt(pos.y())

        if col >= 0:
            rename_action = menu.addAction("✏️ Переименовать колонку")
            type_action = menu.addAction(f"📋 Тип колонки")
            menu.addSeparator()
            insert_left = menu.addAction("⬅ Вставить колонку слева")
            insert_right = menu.addAction("➡ Вставить колонку справа")
            menu.addSeparator()
            del_col_action = menu.addAction("❌ Удалить колонку")

        action = menu.exec(self.grid.mapToGlobal(pos))
        if col >= 0:
            if action == rename_action:
                self.rename_column(col)
            elif action == type_action:
                self.change_column_type(col)
            elif action == del_col_action:
                self.grid.removeColumn(col)
            elif action == insert_left:
                self.grid.insertColumn(col)
                self.grid.setHorizontalHeaderItem(col, QTableWidgetItem("new"))
            elif action == insert_right:
                self.grid.insertColumn(col + 1)
                self.grid.setHorizontalHeaderItem(col + 1, QTableWidgetItem("new"))

    def rename_column(self, col):
        old = self.grid.horizontalHeaderItem(col)
        old_text = old.text() if old else ""
        new_text, ok = QInputDialog.getText(self, "Переименовать колонку",
                                           "Новое имя:", text=old_text)
        if ok and new_text:
            self.grid.setHorizontalHeaderItem(col, QTableWidgetItem(new_text))

    def change_column_type(self, col):
        dlg = ColumnTypeDialog('TEXT', self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if not hasattr(self, '_new_col_types'):
                self._new_col_types = {}
            header = self.grid.horizontalHeaderItem(col)
            if header:
                self._new_col_types[header.text()] = dlg.get_type()

    def save_data(self):
        if not self.db_manager or not self.db_manager.connection:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте базу данных!")
            return

        table_name = self.current_table
        if not table_name:
            name, ok = QInputDialog.getText(self, "Сохранить как", "Имя новой таблицы:")
            if not ok or not name or not validate_table_name(name.strip()):
                QMessageBox.warning(self, "Ошибка", "Некорректное имя таблицы!")
                return
            table_name = name.strip()

            grid_cols = []
            type_map = getattr(self, '_new_col_types', {})
            for c in range(self.grid.columnCount()):
                header = self.grid.horizontalHeaderItem(c)
                col_name = header.text() if header else f"col{c+1}"
                grid_cols.append(col_name)

            col_defs = []
            for col_name in grid_cols:
                col_type = type_map.get(col_name, 'TEXT')
                col_defs.append({'name': col_name, 'type': col_type,
                               'pk': False, 'notnull': False, 'default': ''})
            col_defs[0]['pk'] = True

            success, err = self.db_manager.create_table(table_name, col_defs)
            if not success:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать таблицу:\n{err}")
                return

            self.current_table = table_name
            self.refresh_table_list()
            idx = self.table_selector.findText(table_name)
            if idx >= 0:
                self.table_selector.setCurrentIndex(idx)

        try:
            cursor = self.db_manager.connection.cursor()

            cursor.execute(f'PRAGMA table_info("{table_name}")')
            existing_cols = {row[1] for row in cursor.fetchall()}

            grid_cols = []
            for c in range(self.grid.columnCount()):
                header = self.grid.horizontalHeaderItem(c)
                name = header.text() if header else f"col{c+1}"
                grid_cols.append(name)

            new_col_types = getattr(self, '_new_col_types', {})
            for col_name in grid_cols:
                if col_name not in existing_cols:
                    col_type = new_col_types.get(col_name, 'TEXT')
                    cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{col_name}" {col_type}')

            cursor.execute(f'DELETE FROM "{table_name}"')

            col_names = ', '.join(f'"{c}"' for c in grid_cols)
            placeholders = ', '.join('?' for _ in grid_cols)

            for r in range(self.grid.rowCount()):
                values = []
                for c in range(len(grid_cols)):
                    item = self.grid.item(r, c)
                    values.append(item.text() if item and item.text() else None)
                cursor.execute(f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})', values)

            self.db_manager.connection.commit()
            self._new_col_types = {}

            models_logger.info(f"Данные сохранены в {table_name}")
            QMessageBox.information(self, "Успех", "Данные сохранены!")
            self.load_schema_info(table_name)
            self.refresh_relations()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{e}")
