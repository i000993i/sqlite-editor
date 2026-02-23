import sys
import sqlite3
import pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import json
import csv
from datetime import datetime
import os

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Проверяем наличие кастомного фона
        splash_image = QPixmap(400, 300)
        
        # Пытаемся загрузить кастомный фон из папки fon
        custom_bg_path = os.path.join("fon", "splash.png")
        if os.path.exists(custom_bg_path):
            custom_bg = QPixmap(custom_bg_path)
            if not custom_bg.isNull():
                splash_image = custom_bg.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                               Qt.TransformationMode.SmoothTransformation)
            else:
                splash_image.fill(QColor(40, 0, 0))  # Темно-красный фон по умолчанию
        else:
            splash_image.fill(QColor(40, 0, 0))  # Темно-красный фон
        
        super().__init__(splash_image)
        
        self.label = QLabel(self)
        self.label.setGeometry(50, 150, 300, 50)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #ff4444; background-color: rgba(0,0,0,0.7); border-radius: 10px;")
        self.label.setText("SQLite Table Viewer")
        
        self.progress = QProgressBar(self)
        self.progress.setGeometry(50, 220, 300, 20)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #8b0000;
                border-radius: 5px;
                text-align: center;
                background-color: rgba(0,0,0,0.5);
            }
            QProgressBar::chunk {
                background-color: #8b0000;
                border-radius: 3px;
            }
        """)

class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        sql_keywords = [
            "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER",
            "TABLE", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL",
            "ON", "AND", "OR", "NOT", "NULL", "IS", "LIKE", "IN", "BETWEEN",
            "VALUES", "SET", "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET"
        ]
        
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(255, 100, 100))  # Красный для ключевых слов
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        for word in sql_keywords:
            pattern = f"\\b{word}\\b"
            rule = (QRegularExpression(pattern, QRegularExpression.PatternOption.CaseInsensitiveOption), 
                   keyword_format)
            self.highlighting_rules.append(rule)
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(255, 150, 50))  # Оранжевый для строк
        rule = (QRegularExpression("'.*'"), string_format)
        self.highlighting_rules.append(rule)
        rule = (QRegularExpression("\".*\""), string_format)
        self.highlighting_rules.append(rule)
        
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(255, 200, 100))  # Желтый для чисел
        rule = (QRegularExpression("\\b\\d+\\b"), number_format)
        self.highlighting_rules.append(rule)
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(150, 150, 150))
        comment_format.setFontItalic(True)
        rule = (QRegularExpression("--[^\n]*"), comment_format)
        self.highlighting_rules.append(rule)
        rule = (QRegularExpression("/\\*.*\\*/"), comment_format)
        self.highlighting_rules.append(rule)
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

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
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        # Панель управления
        control_layout = QHBoxLayout()
        
        # Поиск
        search_label = QLabel("🔍 Поиск:")
        search_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #8b0000;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus {
                border-color: #ff4444;
            }
        """)
        self.search_input.textChanged.connect(self.filter_table)
        
        # Лимит записей
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["100", "500", "1000", "5000", "10000", "Все"])
        self.limit_combo.setCurrentText("1000")
        self.limit_combo.setStyleSheet(self.get_combo_style())
        self.limit_combo.currentTextChanged.connect(self.change_limit)
        
        # Кнопка обновления
        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.setStyleSheet(self.get_button_style())
        self.refresh_btn.clicked.connect(self.refresh_table)
        
        # Информация о количестве записей
        self.record_count_label = QLabel("Записей: 0")
        self.record_count_label.setStyleSheet("color: #888; padding: 5px;")
        
        control_layout.addWidget(search_label)
        control_layout.addWidget(self.search_input)
        control_layout.addStretch()
        control_layout.addWidget(QLabel("Лимит:"))
        control_layout.addWidget(self.limit_combo)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.record_count_label)
        
        # Таблица
        self.table = QTableView()
        self.table.setStyleSheet("""
            QTableView {
                background-color: #1a1a1a;
                color: white;
                gridline-color: #8b0000;
                border: 2px solid #8b0000;
                border-radius: 5px;
            }
            QTableView::item {
                padding: 5px;
            }
            QTableView::item:selected {
                background-color: #003366;  /* Темно-синий для выделения */
                color: white;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ff4444;
                padding: 5px;
                border: 1px solid #8b0000;
                font-weight: bold;
            }
        """)
        
        # Используем кастомную модель для больших данных
        self.model = LargeTableModel()
        self.table.setModel(self.model)
        
        # Включаем сортировку
        self.table.setSortingEnabled(True)
        
        layout.addLayout(control_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        self.current_data = []
        self.current_headers = []
        self.current_limit = 1000
        self.current_table = None
        self.db_connection = None
    
    def get_combo_style(self):
        return """
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #8b0000;
                border-radius: 5px;
                padding: 5px;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ff4444;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #003366;
                selection-color: white;
            }
        """
    
    def get_button_style(self):
        return """
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #8b0000;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8b0000;
                color: white;
                border-color: #ff4444;
            }
            QPushButton:pressed {
                background-color: #660000;
            }
        """
    
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
        
        # Показываем количество найденных записей
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
        
        # Подгоняем колонки
        self.table.resizeColumnsToContents()
        
        # Обновляем информацию
        if self.current_limit and total_count > self.current_limit:
            self.record_count_label.setText(f"Показано: {len(data)} из {total_count} (ограничено)")
        else:
            self.record_count_label.setText(f"Записей: {len(data)}")
    
    def clear(self):
        self.current_data = []
        self.current_headers = []
        self.current_table = None
        self.model.update_data([], [])
        self.record_count_label.setText("Записей: 0")

class SQLiteEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_db = None
        self.connection = None
        self.query_history = []
        self.init_ui()
        self.load_styles()
        self.show_splash()
    
    def show_splash(self):
        self.splash = SplashScreen()
        self.splash.show()
        
        for i in range(101):
            self.splash.progress.setValue(i)
            QApplication.processEvents()
            QThread.msleep(20)
        
        self.splash.close()
        self.show()
    
    def load_styles(self):
        # Устанавливаем общий фон для главного окна
        bg_image_path = os.path.join("fon", "background.png")
        if os.path.exists(bg_image_path):
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-image: url({bg_image_path});
                    background-repeat: no-repeat;
                    background-position: center;
                }}
                QMenuBar {{
                    background-color: rgba(45, 45, 45, 200);
                    color: white;
                    border-bottom: 2px solid #8b0000;
                }}
                QMenuBar::item {{
                    background-color: transparent;
                    padding: 5px 10px;
                }}
                QMenuBar::item:selected {{
                    background-color: #8b0000;
                    color: white;
                }}
                QMenu {{
                    background-color: rgba(45, 45, 45, 240);
                    color: white;
                    border: 1px solid #8b0000;
                }}
                QMenu::item:selected {{
                    background-color: #8b0000;
                    color: white;
                }}
                QStatusBar {{
                    background-color: rgba(45, 45, 45, 200);
                    color: white;
                    border-top: 1px solid #8b0000;
                }}
                QTabWidget::pane {{
                    border: 2px solid #8b0000;
                    border-radius: 5px;
                    background-color: rgba(30, 30, 30, 240);
                }}
                QTabBar::tab {{
                    background-color: rgba(45, 45, 45, 200);
                    color: white;
                    padding: 8px 15px;
                    margin-right: 2px;
                    border-top-left-radius: 5px;
                    border-top-right-radius: 5px;
                }}
                QTabBar::tab:selected {{
                    background-color: #8b0000;
                    color: white;
                }}
                QTabBar::tab:hover:!selected {{
                    background-color: #660000;
                }}
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1a1a1a;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: white;
                    border-bottom: 2px solid #8b0000;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 5px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #8b0000;
                    color: white;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: white;
                    border: 1px solid #8b0000;
                }
                QMenu::item:selected {
                    background-color: #8b0000;
                    color: white;
                }
                QStatusBar {
                    background-color: #2d2d2d;
                    color: white;
                    border-top: 1px solid #8b0000;
                }
                QTabWidget::pane {
                    border: 2px solid #8b0000;
                    border-radius: 5px;
                    background-color: #1e1e1e;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: white;
                    padding: 8px 15px;
                    margin-right: 2px;
                    border-top-left-radius: 5px;
                    border-top-right-radius: 5px;
                }
                QTabBar::tab:selected {
                    background-color: #8b0000;
                    color: white;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #660000;
                }
            """)
    
    def init_ui(self):
        self.setWindowTitle("SQLite Table Viewer")
        self.setGeometry(100, 100, 1400, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        self.create_menu()
        self.create_toolbar()
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        main_splitter.setSizes([300, 1100])
        
        main_layout.addWidget(main_splitter)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
    
    def create_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Файл")
        
        open_action = QAction("📂 Открыть базу данных", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_database)
        file_menu.addAction(open_action)
        
        new_action = QAction("🆕 Создать базу данных", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.create_database)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        import_menu = file_menu.addMenu("📥 Импорт")
        import_csv = QAction("Из CSV", self)
        import_csv.triggered.connect(self.import_csv)
        import_menu.addAction(import_csv)
        import_json = QAction("Из JSON", self)
        import_json.triggered.connect(self.import_json)
        import_menu.addAction(import_json)
        
        export_menu = file_menu.addMenu("📤 Экспорт")
        export_csv = QAction("В CSV", self)
        export_csv.triggered.connect(self.export_csv)
        export_menu.addAction(export_csv)
        export_json = QAction("В JSON", self)
        export_json.triggered.connect(self.export_json)
        export_menu.addAction(export_json)
        export_excel = QAction("В Excel", self)
        export_excel.triggered.connect(self.export_excel)
        export_menu.addAction(export_excel)
        
        file_menu.addSeparator()
        
        exit_action = QAction("❌ Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("Правка")
        
        copy_action = QAction("📋 Копировать", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_selected)
        edit_menu.addAction(copy_action)
        
        find_action = QAction("🔍 Найти", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.find_in_table)
        edit_menu.addAction(find_action)
        
        tools_menu = menubar.addMenu("🔧 Инструменты")
        
        backup_action = QAction("💾 Создать резервную копию", self)
        backup_action.triggered.connect(self.backup_database)
        tools_menu.addAction(backup_action)
        
        optimize_action = QAction("⚡ Оптимизировать базу данных", self)
        optimize_action.triggered.connect(self.optimize_database)
        tools_menu.addAction(optimize_action)
        
        tools_menu.addSeparator()
        
        history_action = QAction("📜 История запросов", self)
        history_action.triggered.connect(self.show_history)
        tools_menu.addAction(history_action)
        
        help_menu = menubar.addMenu("❓ Справка")
        
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: rgba(45, 45, 45, 200);
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #8b0000;
                color: white;
            }
        """)
        
        actions = [
            ("📂 Открыть", self.open_database),
            ("📥 Импорт", self.import_csv),
            ("📤 Экспорт", self.export_csv),
        ]
        
        for text, func in actions:
            action = QAction(text, self)
            action.triggered.connect(func)
            toolbar.addAction(action)
            toolbar.addSeparator()
        
        self.addToolBar(toolbar)
    
    def create_left_panel(self):
        panel = QWidget()
        
        # Устанавливаем полупрозрачный фон для панели
        panel.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 200);
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        title = QLabel("📁 Таблицы")
        title.setStyleSheet("""
            QLabel {
                color: #ff4444;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: rgba(45, 45, 45, 200);
                border-radius: 5px;
                border: 1px solid #8b0000;
            }
        """)
        layout.addWidget(title)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Имя таблицы")
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(45, 45, 45, 200);
                color: white;
                border: 2px solid #8b0000;
                border-radius: 5px;
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #003366;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #660000;
            }
        """)
        self.tree.itemDoubleClicked.connect(self.load_table)
        layout.addWidget(self.tree)
        
        self.db_info = QLabel()
        self.db_info.setStyleSheet("""
            QLabel {
                color: #888;
                padding: 10px;
                background-color: rgba(45, 45, 45, 200);
                border-radius: 5px;
                margin-top: 10px;
                border: 1px solid #8b0000;
            }
        """)
        layout.addWidget(self.db_info)
        
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        panel = QWidget()
        
        # Устанавливаем полупрозрачный фон для панели
        panel.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 200);
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        
        # Вкладка с таблицей
        self.data_viewer = TableViewer()
        self.tabs.addTab(self.data_viewer, "📊 Просмотр таблицы")
        
        # Вкладка SQL
        sql_widget = QWidget()
        sql_layout = QVBoxLayout()
        
        sql_toolbar = QHBoxLayout()
        
        self.execute_btn = QPushButton("▶ Выполнить (F5)")
        self.execute_btn.setStyleSheet(self.get_button_style())
        self.execute_btn.clicked.connect(self.execute_query)
        sql_toolbar.addWidget(self.execute_btn)
        
        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.setStyleSheet(self.get_button_style())
        self.clear_btn.clicked.connect(lambda: self.sql_input.clear())
        sql_toolbar.addWidget(self.clear_btn)
        
        sql_toolbar.addStretch()
        
        self.sql_input = QTextEdit()
        self.sql_input.setPlaceholderText("Введите SQL запрос...")
        self.sql_input.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                border: 2px solid #8b0000;
                border-radius: 5px;
                padding: 10px;
            }
            QTextEdit:focus {
                border-color: #ff4444;
            }
        """)
        
        self.highlighter = SQLHighlighter(self.sql_input.document())
        
        sql_layout.addLayout(sql_toolbar)
        sql_layout.addWidget(self.sql_input)
        
        sql_widget.setLayout(sql_layout)
        self.tabs.addTab(sql_widget, "📝 SQL запросы")
        
        layout.addWidget(self.tabs)
        panel.setLayout(layout)
        
        return panel
    
    def get_button_style(self):
        return """
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #8b0000;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8b0000;
                color: white;
                border-color: #ff4444;
            }
            QPushButton:pressed {
                background-color: #660000;
            }
        """
    
    def open_database(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Открыть базу данных", 
            "", 
            "SQLite files (*.db *.sqlite *.db3);;All files (*.*)"
        )
        
        if file_path:
            try:
                self.current_db = file_path
                self.connection = sqlite3.connect(file_path)
                self.connection.execute("PRAGMA journal_mode=WAL")
                
                # Передаем соединение в TableViewer
                self.data_viewer.set_connection(self.connection)
                
                self.load_tables()
                
                file_size = os.path.getsize(file_path)
                size_str = self.format_size(file_size)
                self.db_info.setText(f"📊 {os.path.basename(file_path)}\n📦 Размер: {size_str}")
                
                self.status_bar.showMessage(f"База данных загружена: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть базу данных: {str(e)}")
    
    def format_size(self, size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"
    
    def load_tables(self):
        self.tree.clear()
        
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                
                # Получаем количество записей
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                
                # Создаем элемент с информацией о количестве записей
                item = QTreeWidgetItem([f"{table_name} ({count} записей)"])
                item.setData(0, Qt.ItemDataRole.UserRole, table_name)
                
                self.tree.addTopLevelItem(item)
    
    def load_table(self, item):
        # Получаем имя таблицы из UserRole
        table_name = item.data(0, Qt.ItemDataRole.UserRole)
        
        if table_name:
            self.data_viewer.load_table_data(table_name)
            self.tabs.setCurrentIndex(0)  # Переключаемся на вкладку просмотра
            self.status_bar.showMessage(f"Загружена таблица {table_name}")
    
    def execute_query(self):
        if not self.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        query = self.sql_input.toPlainText().strip()
        if not query:
            return
        
        try:
            self.query_history.append({
                'query': query,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            if query.upper().strip().startswith("SELECT"):
                data = cursor.fetchall()
                columns = [description[0] for description in cursor.description] if cursor.description else []
                
                # Ограничиваем отображение для очень больших результатов
                if len(data) > 10000:
                    QMessageBox.information(self, "Информация", 
                                          f"Получено {len(data)} записей. Показаны первые 10000.")
                    data = data[:10000]
                
                self.data_viewer.current_data = data
                self.data_viewer.current_headers = columns
                self.data_viewer.model.update_data(data, columns)
                self.data_viewer.table.resizeColumnsToContents()
                
                self.status_bar.showMessage(f"Запрос выполнен. Получено строк: {len(data)}")
                self.tabs.setCurrentIndex(0)
            
            else:
                self.connection.commit()
                self.status_bar.showMessage(f"Запрос выполнен. Затронуто строк: {cursor.rowcount}")
                self.load_tables()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка выполнения запроса:\n{str(e)}")
    
    def import_csv(self):
        if not self.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Импорт CSV", "", "CSV files (*.csv)")
        if file_path:
            try:
                chunk_size = 10000
                table_name = os.path.splitext(os.path.basename(file_path))[0]
                
                first_chunk = True
                for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                    if first_chunk:
                        chunk.to_sql(table_name, self.connection, if_exists='replace', index=False)
                        first_chunk = False
                    else:
                        chunk.to_sql(table_name, self.connection, if_exists='append', index=False)
                
                self.load_tables()
                QMessageBox.information(self, "Успех", f"Данные импортированы в таблицу {table_name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка импорта: {str(e)}")
    
    def import_json(self):
        if not self.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Импорт JSON", "", "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                df = pd.DataFrame(data)
                table_name = os.path.splitext(os.path.basename(file_path))[0]
                
                df.to_sql(table_name, self.connection, if_exists='replace', index=False)
                
                self.load_tables()
                QMessageBox.information(self, "Успех", f"Данные импортированы в таблицу {table_name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка импорта: {str(e)}")
    
    def export_csv(self):
        if not self.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        table_name, ok = QInputDialog.getItem(self, "Экспорт", "Выберите таблицу:", 
                                             self.get_table_names(), 0, False)
        if ok and table_name:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", 
                                                      f"{table_name}.csv", "CSV files (*.csv)")
            if file_path:
                try:
                    chunk_size = 10000
                    first_chunk = True
                    
                    for chunk in pd.read_sql_query(f"SELECT * FROM {table_name}", 
                                                   self.connection, chunksize=chunk_size):
                        if first_chunk:
                            chunk.to_csv(file_path, index=False, encoding='utf-8')
                            first_chunk = False
                        else:
                            chunk.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8')
                    
                    QMessageBox.information(self, "Успех", f"Таблица экспортирована в {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def export_json(self):
        if not self.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        table_name, ok = QInputDialog.getItem(self, "Экспорт", "Выберите таблицу:", 
                                             self.get_table_names(), 0, False)
        if ok and table_name:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить JSON", 
                                                      f"{table_name}.json", "JSON files (*.json)")
            if file_path:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.connection)
                    df.to_json(file_path, orient='records', indent=2, force_ascii=False)
                    QMessageBox.information(self, "Успех", f"Таблица экспортирована в {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def export_excel(self):
        if not self.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        table_name, ok = QInputDialog.getItem(self, "Экспорт", "Выберите таблицу:", 
                                             self.get_table_names(), 0, False)
        if ok and table_name:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить Excel", 
                                                      f"{table_name}.xlsx", "Excel files (*.xlsx)")
            if file_path:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1000000", self.connection)
                    if len(df) == 1000000:
                        QMessageBox.information(self, "Информация", 
                                              "Экспортировано 1,000,000 записей (максимум для Excel)")
                    
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name=table_name, index=False)
                    
                    QMessageBox.information(self, "Успех", f"Таблица экспортирована в {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def get_table_names(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [table[0] for table in cursor.fetchall()]
    
    def create_database(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Создать базу данных", 
                                                   "database.db", "SQLite files (*.db)")
        if file_path:
            try:
                self.connection = sqlite3.connect(file_path)
                self.connection.execute("PRAGMA journal_mode=WAL")
                self.current_db = file_path
                self.data_viewer.set_connection(self.connection)
                self.load_tables()
                self.status_bar.showMessage(f"Создана база данных: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать базу данных: {str(e)}")
    
    def copy_selected(self):
        focused = self.focusWidget()
        if isinstance(focused, QTextEdit):
            focused.copy()
        elif isinstance(focused, QTableView):
            selection = self.data_viewer.table.selectedIndexes()
            if selection:
                text = ''
                current_row = selection[0].row()
                for index in selection:
                    if index.row() != current_row:
                        text += '\n'
                        current_row = index.row()
                    text += index.data() + '\t'
                QApplication.clipboard().setText(text)
    
    def find_in_table(self):
        # Поиск уже реализован в TableViewer
        self.tabs.setCurrentIndex(0)
        self.data_viewer.search_input.setFocus()
    
    def backup_database(self):
        if not self.current_db:
            QMessageBox.warning(self, "Предупреждение", "Нет открытой базы данных!")
            return
        
        backup_path = self.current_db + ".backup"
        try:
            import shutil
            shutil.copy2(self.current_db, backup_path)
            QMessageBox.information(self, "Успех", f"Резервная копия создана: {backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать резервную копию: {str(e)}")
    
    def optimize_database(self):
        if not self.connection:
            QMessageBox.warning(self, "Предупреждение", "Нет открытой базы данных!")
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("VACUUM;")
            QMessageBox.information(self, "Успех", "База данных оптимизирована")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось оптимизировать БД: {str(e)}")
    
    def show_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("История запросов")
        dialog.setGeometry(200, 200, 600, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: rgba(45, 45, 45, 240);
            }
            QListWidget {
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #8b0000;
                border-radius: 5px;
                font-family: monospace;
            }
            QListWidget::item:selected {
                background-color: #003366;
            }
        """)
        
        layout = QVBoxLayout()
        
        list_widget = QListWidget()
        for item in self.query_history[-50:]:
            list_widget.addItem(f"[{item['time']}] {item['query'][:100]}...")
        
        list_widget.itemDoubleClicked.connect(lambda item: self.load_history_query(item, dialog))
        
        layout.addWidget(QLabel("Дважды кликните для загрузки запроса:"))
        layout.addWidget(list_widget)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def load_history_query(self, item, dialog):
        # Здесь можно реализовать загрузку запроса из истории
        dialog.accept()
    
    def show_about(self):
        QMessageBox.about(self, "О программе", 
                         """<h1>SQLite Table Viewer</h1>
                         <p>Версия: 1.0</p>
                         <p>Простой просмотрщик таблиц SQLite</p>
                         <p>Особенности:</p>
                         <ul>
                             <li>Просмотр таблиц с настраиваемым лимитом записей</li>
                             <li>Поиск по таблице</li>
                             <li>Выполнение SQL запросов</li>
                             <li>Импорт/экспорт в CSV, JSON, Excel</li>
                             <li>Подсветка синтаксиса SQL</li>
                         </ul>
                         <p style="color: #ff4444;">Разработано с любовью к данным ❤️</p>""")
    
    def closeEvent(self, event):
        if self.connection:
            self.connection.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SQLiteEditor()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()