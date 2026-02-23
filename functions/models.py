from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class LargeTableModel(QAbstractTableModel):
    """Модель для работы с большими данными"""
    def __init__(self, data=None, headers=None):
        super().__init__()
        self._data = data if data is not None else []
        self._headers = headers if headers is not None else []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers) if self._headers else 0
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            if 0 <= row < len(self._data) and 0 <= col < len(self._data[row]):
                return str(self._data[row][col])
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._headers):
                    return self._headers[section]
            else:
                return str(section + 1)
        return QVariant()
    
    def update_data(self, data, headers):
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self.endResetModel()

class TableViewer(QWidget):
    def __init__(self, icon_manager=None, parent=None):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self.current_data = []
        self.current_headers = []
        self.current_limit = 1000
        self.current_table = None
        self.db_connection = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Панель управления
        control_layout = QHBoxLayout()
        
        # Поиск с иконкой
        search_layout = QHBoxLayout()
        
        if self.icon_manager:
            search_icon_label = QLabel()
            search_icon_label.setPixmap(self.icon_manager.get_icon('search').pixmap(20, 20))
            search_layout.addWidget(search_icon_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по таблице...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #303030;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #505050;
            }
        """)
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        
        control_layout.addLayout(search_layout)
        control_layout.addStretch()
        
        # Лимит записей с иконкой
        if self.icon_manager:
            limit_icon_label = QLabel()
            limit_icon_label.setPixmap(self.icon_manager.get_icon('limit').pixmap(20, 20))
            control_layout.addWidget(limit_icon_label)
        
        control_layout.addWidget(QLabel("Лимит:"))
        
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["100", "500", "1000", "5000", "10000", "Все"])
        self.limit_combo.setCurrentText("1000")
        self.limit_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #303030;
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }
            QComboBox:hover {
                border-color: #404040;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #303030;
                selection-background-color: #303030;
            }
        """)
        self.limit_combo.currentTextChanged.connect(self.change_limit)
        control_layout.addWidget(self.limit_combo)
        
        # Кнопка обновления с иконкой
        self.refresh_btn = QPushButton()
        if self.icon_manager:
            self.icon_manager.set_button_icon(self.refresh_btn, 'refresh')
        else:
            self.refresh_btn.setText("🔄")
        self.refresh_btn.setToolTip("Обновить данные")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #303030;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #252525;
                border-color: #404040;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_table)
        control_layout.addWidget(self.refresh_btn)
        
        # Информация о записях
        self.record_count_label = QLabel("0 записей")
        self.record_count_label.setStyleSheet("color: #808080; padding: 5px;")
        control_layout.addWidget(self.record_count_label)
        
        # Таблица
        self.table = QTableView()
        self.table.setStyleSheet("""
            QTableView {
                background-color: #1a1a1a;
                color: #e0e0e0;
                gridline-color: #303030;
                border: 1px solid #303030;
                border-radius: 3px;
                selection-background-color: #404040;
                selection-color: #ffffff;
            }
            QTableView::item {
                padding: 5px;
                border-bottom: 1px solid #252525;
            }
            QTableView::item:selected {
                background-color: #404040;
            }
            QHeaderView::section {
                background-color: #202020;
                color: #a0a0a0;
                padding: 8px 5px;
                border: none;
                border-right: 1px solid #303030;
                border-bottom: 1px solid #303030;
                font-weight: bold;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QTableCornerButton::section {
                background-color: #202020;
                border: none;
                border-bottom: 1px solid #303030;
            }
        """)
        
        self.model = LargeTableModel()
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        
        layout.addLayout(control_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
    
    def set_connection(self, connection):
        self.db_connection = connection
    
    def filter_table(self, text):
        if not self.current_data:
            return
        
        for row in range(self.model.rowCount()):
            show_row = False
            for col in range(self.model.columnCount()):
                index = self.model.index(row, col)
                value = str(self.model.data(index))
                if text.lower() in value.lower():
                    show_row = True
                    break
            self.table.setRowHidden(row, not show_row)
        
        visible_count = sum(1 for row in range(self.model.rowCount()) 
                           if not self.table.isRowHidden(row))
        self.record_count_label.setText(f"Показано: {visible_count} из {len(self.current_data)}")
    
    def change_limit(self, limit_text):
        if limit_text == "Все":
            self.current_limit = None
        else:
            self.current_limit = int(limit_text)
    
    def refresh_table(self):
        if self.current_table and self.db_connection:
            self.load_table_data(self.current_table)
    
    def load_table_data(self, table_name):
        self.current_table = table_name
        
        cursor = self.db_connection.cursor()
        
        # Получаем общее количество записей
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        total_count = cursor.fetchone()[0]
        
        # Загружаем данные с лимитом
        if self.current_limit:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {self.current_limit};")
        else:
            cursor.execute(f"SELECT * FROM {table_name};")
        
        data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        self.current_data = data
        self.current_headers = columns
        self.model.update_data(data, columns)
        
        self.table.resizeColumnsToContents()
        
        if self.current_limit and total_count > self.current_limit:
            self.record_count_label.setText(f"Показано {len(data)} из {total_count}")
        else:
            self.record_count_label.setText(f"Всего записей: {len(data)}")
    
    def clear(self):
        self.current_data = []
        self.current_headers = []
        self.current_table = None
        self.model.update_data([], [])
        self.record_count_label.setText("0 записей")