from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from functions.virtual_table_model import VirtualTableModel
from functions.async_manager import SchemaCache
from functions.logger import models_logger
from functions.utils import validate_table_name, validate_column_name
from functions.table_designer import COLUMN_TYPES
from functions.styles import Styles
from typing import Optional

class ProgressOverlay(QWidget):

    _progress_signal = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(50, 50, 50, 50)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 240);
                border: 2px solid #404040;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)

        self.loading_label = QLabel("⏳")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self.loading_label)

        self.status_label = QLabel("Загрузка данных...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #e0e0e0; font-size: 14px; padding: 10px 0;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #1a1a1a; border: 1px solid #303030;
                border-radius: 3px; text-align: center; height: 20px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #408040, stop:1 #60a060); border-radius: 2px; }
        """)
        layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setStyleSheet("""
            QPushButton { background-color: #804040; color: white; border: none;
                border-radius: 5px; padding: 8px 20px; font-weight: bold; }
            QPushButton:hover { background-color: #a05050; }
        """)
        self.cancel_button.clicked.connect(self.cancel_operation)
        layout.addWidget(self.cancel_button)

        outer.addWidget(container)

        self._cancel_callback = None
        self._animation = None
        self._progress_signal.connect(self._update_progress)

    def set_cancel_callback(self, callback):
        self._cancel_callback = callback

    def cancel_operation(self):
        if self._cancel_callback:
            self._cancel_callback()
        self.hide()

    def show_progress(self, percent: int, message: str):
        self._progress_signal.emit(percent, message)

    def _update_progress(self, percent: int, message: str):
        self.progress_bar.setValue(percent)
        if message:
            self.status_label.setText(message)

    def show_blocking(self, message: str = "Пожалуйста, подождите..."):
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 0)
        self.show()
        self.raise_()

    def hide_blocking(self):
        self.progress_bar.setRange(0, 100)
        self.hide()


class TableViewerVirtual(QWidget):

    def __init__(self, icon_manager=None, parent=None):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self.db_connection = None
        self.db_manager = None
        self.schema_cache = SchemaCache()

        self.current_table = None
        self.current_page = 0
        self.page_size = 100
        self.total_rows = 0
        self.visible_rows = 0
        self._table_loaded = False
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)

        self.model = VirtualTableModel(page_size=self.page_size)
        self.model.page_loaded.connect(self.on_page_loaded)
        self.model.search_started.connect(self.on_search_started)
        self.model.search_finished.connect(self.on_search_finished)
        self.model.error_occurred.connect(self.on_error)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        control_layout = QHBoxLayout()

        search_layout = QHBoxLayout()
        if self.icon_manager:
            search_icon_label = QLabel()
            search_icon_label.setPixmap(self.icon_manager.get_icon('search').pixmap(20, 20))
            search_layout.addWidget(search_icon_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по таблице...")
        self.search_input.setStyleSheet(Styles.LINE_EDIT)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)
        control_layout.addLayout(search_layout)
        control_layout.addStretch()

        self.pagination_label = QLabel("Страница 0 / 0")
        self.pagination_label.setStyleSheet("color: #808080; padding: 5px;")
        control_layout.addWidget(self.pagination_label)

        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(40)
        prev_btn.clicked.connect(self.previous_page)
        control_layout.addWidget(prev_btn)

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setRange(0, 0)
        self.page_spinbox.setStyleSheet("""
            QSpinBox { background-color: #1a1a1a; color: #e0e0e0;
                border: 1px solid #303030; border-radius: 3px;
                padding: 3px 10px; min-width: 80px; }
        """)
        self.page_spinbox.valueChanged.connect(self.go_to_page)
        control_layout.addWidget(self.page_spinbox)

        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(40)
        next_btn.clicked.connect(self.next_page)
        control_layout.addWidget(next_btn)

        control_layout.addWidget(QLabel("Строк на стр:"))

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["50", "100", "200", "500", "1000"])
        self.page_size_combo.setCurrentText("100")
        self.page_size_combo.setStyleSheet(Styles.COMBO_BOX)
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        control_layout.addWidget(self.page_size_combo)

        self.refresh_btn = QPushButton()
        if self.icon_manager:
            self.icon_manager.set_button_icon(self.refresh_btn, 'refresh')
        else:
            self.refresh_btn.setText("🔄")
        self.refresh_btn.setToolTip("Обновить данные")
        self.refresh_btn.clicked.connect(self.refresh_table)
        control_layout.addWidget(self.refresh_btn)

        self.record_count_label = QLabel("0 записей")
        self.record_count_label.setStyleSheet("color: #808080; padding: 5px;")
        control_layout.addWidget(self.record_count_label)

        self.edit_mode_btn = QPushButton("✏️ Правка")
        self.edit_mode_btn.setCheckable(True)
        self.edit_mode_btn.setToolTip("Включить редактирование ячеек")
        self.edit_mode_btn.setStyleSheet(Styles.TOGGLE_BUTTON)
        self.edit_mode_btn.toggled.connect(self.toggle_edit_mode)
        control_layout.addWidget(self.edit_mode_btn)

        self.add_row_btn = QPushButton("➕ Строка")
        self.add_row_btn.setToolTip("Добавить строку")
        self.add_row_btn.setStyleSheet("""
            QPushButton { background-color: #2a4a2a; color: white; border: none;
                border-radius: 3px; padding: 5px 10px; }
            QPushButton:hover { background-color: #3a6a3a; }
        """)
        self.add_row_btn.clicked.connect(self.add_row)
        control_layout.addWidget(self.add_row_btn)

        self.del_row_btn = QPushButton("➖ Строка")
        self.del_row_btn.setToolTip("Удалить выбранные строки")
        self.del_row_btn.setStyleSheet("""
            QPushButton { background-color: #5a2d2d; color: white; border: none;
                border-radius: 3px; padding: 5px 10px; }
            QPushButton:hover { background-color: #7a3d3d; }
        """)
        self.del_row_btn.clicked.connect(self.delete_row)
        control_layout.addWidget(self.del_row_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #303030;")
        control_layout.addWidget(sep)

        self.add_col_btn = QPushButton("➕ Колонка")
        self.add_col_btn.setToolTip("Добавить колонку")
        self.add_col_btn.setStyleSheet("""
            QPushButton { background-color: #2d4a5a; color: white; border: none;
                border-radius: 3px; padding: 5px 10px; }
            QPushButton:hover { background-color: #3d6a7a; }
        """)
        self.add_col_btn.clicked.connect(self.add_column)
        control_layout.addWidget(self.add_col_btn)

        self.del_col_btn = QPushButton("➖ Колонка")
        self.del_col_btn.setToolTip("Удалить выбранную колонку")
        self.del_col_btn.setStyleSheet("""
            QPushButton { background-color: #5a2d5a; color: white; border: none;
                border-radius: 3px; padding: 5px 10px; }
            QPushButton:hover { background-color: #7a3d7a; }
        """)
        self.del_col_btn.clicked.connect(self.drop_column)
        control_layout.addWidget(self.del_col_btn)

        self.table = QTableView()
        self.table.setStyleSheet(Styles.TABLE_VIEW)
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.table.horizontalHeader().setToolTip("")

        layout.addLayout(control_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.progress_overlay = ProgressOverlay(self)
        self.progress_overlay.set_cancel_callback(self.cancel_operation)

    def set_connection(self, db_manager):
        self.db_manager = db_manager
        self.db_connection = db_manager.connection if db_manager else None
        self.model.set_connection(db_manager)

    def _on_search_text_changed(self, text):
        if text.strip():
            self._search_timer.start(300)
        else:
            self._search_timer.stop()
            self.model.clear_search()
            if self.current_table:
                self.load_table_data(self.current_table)
            self.record_count_label.setText(f"Показано {self.visible_rows} из {self.total_rows} строк")

    def _do_search(self):
        search_text = self.search_input.text().strip()
        if not search_text or not self.current_table:
            return
        self.start_search()

    def load_table_data(self, table_name):
        if not self.db_connection:
            return
        self.current_table = table_name
        self.current_page = 0
        self._table_loaded = False

        self.progress_overlay.show_blocking(f"Загрузка таблицы {table_name}...")
        QApplication.processEvents()

        def progress_callback(percent: int, message: str):
            self.progress_overlay.show_progress(percent, message)

        worker = self.model.load_table(table_name, progress_callback=progress_callback)
        if worker:
            worker.finished.connect(self.progress_overlay.hide_blocking, Qt.ConnectionType.SingleShotConnection)

    def on_page_loaded(self, page: int, total_rows: int, columns_count: int):
        self.current_page = page
        self.total_rows = total_rows
        self.visible_rows = self.model.get_visible_rows()

        total_pages = (total_rows + self.page_size - 1) // self.page_size
        self.page_spinbox.setRange(0, max(0, total_pages - 1))
        self.page_spinbox.setValue(page)

        self.pagination_label.setText(f"Страница {page + 1} / {total_pages}")
        self.record_count_label.setText(f"Показано {self.visible_rows} из {total_rows} строк")

        if not self._table_loaded:
            self.table.resizeColumnsToContents()
            self._table_loaded = True
            self._update_header_tooltips()

        models_logger.info(f"Страница {page} загружена: {self.visible_rows} строк")

    def _update_header_tooltips(self):
        if not self.db_manager or not self.current_table:
            return
        schema = self.db_manager.get_table_schema(self.current_table)
        if not schema:
            return
        col_info = {c['name']: c for c in schema['columns']}
        header = self.table.horizontalHeader()
        for i in range(self.model.columnCount()):
            name = self.model.headerData(i, Qt.Orientation.Horizontal)
            if name in col_info:
                info = col_info[name]
                tip = f"{info['type']}"
                if info['primary_key']:
                    tip += " [PK]"
                if info['notnull']:
                    tip += " [NOT NULL]"
                if info['default'] is not None:
                    tip += f" default={info['default']}"
                try:
                    header.setSectionToolTip(i, tip)
                except AttributeError:
                    pass

    def on_search_started(self, search_text: str):
        self.progress_overlay.show_blocking(f"Поиск: {search_text}...")
        QApplication.processEvents()

    def on_search_finished(self, results_count: int):
        self.progress_overlay.hide_blocking()
        self.record_count_label.setText(f"Найдено: {results_count} результатов")

    def on_error(self, error_message: str):
        self.progress_overlay.hide_blocking()
        QMessageBox.warning(self, "Ошибка", error_message)
        models_logger.error(f"Ошибка в TableViewer: {error_message}")

    def start_search(self):
        search_text = self.search_input.text().strip()
        if not search_text or not self.current_table:
            return

        self.progress_overlay.show_blocking("Поиск...")
        QApplication.processEvents()

        def progress_callback(percent: int, message: str):
            self.progress_overlay.show_progress(percent, message)

        worker = self.model.search(search_text, limit=1000, progress_callback=progress_callback)
        if worker:
            worker.finished.connect(self.progress_overlay.hide_blocking, Qt.ConnectionType.SingleShotConnection)

    def previous_page(self):
        if self.current_page > 0:
            self.load_page(self.current_page - 1)

    def next_page(self):
        total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.load_page(self.current_page + 1)

    def go_to_page(self, page: int):
        if page != self.current_page:
            self.load_page(page)

    def load_page(self, page: int):
        def progress_callback(percent: int, message: str):
            self.progress_overlay.show_progress(percent, message)
        worker = self.model.load_page(page, progress_callback=progress_callback)
        if worker:
            worker.finished.connect(self.progress_overlay.hide_blocking, Qt.ConnectionType.SingleShotConnection)

    def change_page_size(self, size_str: str):
        self.page_size = int(size_str)
        self.model.page_size = self.page_size
        if self.current_table:
            self.load_table_data(self.current_table)

    def refresh_table(self):
        if self.current_table:
            self.load_table_data(self.current_table)

    def on_scroll(self, value: int):
        scrollbar = self.table.verticalScrollBar()
        max_value = scrollbar.maximum()
        if max_value > 0 and value > max_value * 0.8:
            total_pages = (self.total_rows + self.page_size - 1) // self.page_size
            next_page = self.current_page + 1
            if next_page < total_pages and not self.model.is_loading():
                self.load_page(next_page)

    def toggle_edit_mode(self, checked: bool):
        if checked:
            def update_callback(col_name: str, value, rowid: int):
                table_name = self.model.get_current_table()
                if table_name and self.db_manager:
                    success, error = self.db_manager.update_cell(table_name, col_name, value, rowid)
                    if not success:
                        models_logger.error(f"Ошибка обновления ячейки: {error}")
            self.model.set_update_callback(update_callback)
        else:
            self.model.set_update_callback(None)
        self.model.set_editable(checked)
        self.edit_mode_btn.setText("✅ Правка" if checked else "✏️ Правка")

    def add_row(self):
        if not self.current_table or not self.db_manager:
            return
        col_count = self.model.columnCount()
        values = [""] * col_count
        success, result = self.db_manager.insert_row(self.current_table, values)
        if success:
            self.refresh_table()
            models_logger.info(f"Строка добавлена в {self.current_table}")
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить строку: {result}")

    def delete_row(self):
        if not self.current_table or not self.db_manager:
            return
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Ошибка", "Выберите строки для удаления")
            return
        reply = QMessageBox.question(self, "Подтверждение",
            f"Удалить {len(indexes)} строк(у)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        for idx in sorted(indexes, key=lambda x: x.row(), reverse=True):
            rowid = self.model.get_rowid(idx.row())
            if rowid is not None:
                self.db_manager.delete_row(self.current_table, rowid)
        self.refresh_table()

    def add_column(self):
        if not self.current_table or not self.db_manager:
            return
        name, ok = QInputDialog.getText(self, "Добавить колонку", "Имя колонки:")
        if not ok or not name or not validate_column_name(name.strip()):
            if name:
                QMessageBox.warning(self, "Ошибка", "Некорректное имя колонки!")
            return
        type_name, ok = QInputDialog.getItem(self, "Тип колонки", "Выберите тип:", COLUMN_TYPES, 0, False)
        if not ok:
            return
        success, err = self.db_manager.add_column(self.current_table, name.strip(), type_name)
        if success:
            self.refresh_table()
            models_logger.info(f"Колонка {name} добавлена в {self.current_table}")
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить колонку: {err}")

    def drop_column(self):
        if not self.current_table or not self.db_manager:
            return
        cols = self.model.get_columns()
        if not cols:
            return
        col_name, ok = QInputDialog.getItem(self, "Удалить колонку",
            "Выберите колонку для удаления:", cols, 0, False)
        if not ok or not col_name:
            return
        reply = QMessageBox.question(self, "Подтверждение",
            f"Удалить колонку '{col_name}'? Это удалит все данные в ней.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        success, err = self.db_manager.drop_column(self.current_table, col_name)
        if success:
            self.refresh_table()
            models_logger.info(f"Колонка {col_name} удалена из {self.current_table}")
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить колонку: {err}")

    def cancel_operation(self):
        self.model.cancel()
        self.progress_overlay.hide_blocking()

    def clear(self):
        self.model.cancel()
        self.model.clear_search()
        self.model.beginResetModel()
        self.model._current_table = None
        self.model._data = []
        self.model._columns = []
        self.model._total_rows = 0
        self.model.endResetModel()

        self.current_table = None
        self.current_page = 0
        self.total_rows = 0
        self.visible_rows = 0
        self._table_loaded = False

        self.page_spinbox.setRange(0, 0)
        self.page_spinbox.setValue(0)
        self.pagination_label.setText("Страница 0 / 0")
        self.record_count_label.setText("0 записей")
        self.search_input.clear()
        self.schema_cache.clear()
