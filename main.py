import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from styles import Styles
from database import DatabaseManager
from import_export import ImportExportManager
import utils

class IconManager:
    """Класс для управления SVG иконками"""
    def __init__(self):
        self.icons = {}
        self.icon_size = QSize(20, 20)
        self.load_icons()
    
    def load_icons(self):
        """Загрузка всех SVG иконок"""
        icon_files = {
            'open': 'open.svg',
            'new': 'new.svg',
            'refresh': 'refresh.svg',
            'import': 'import.svg',
            'export': 'export.svg',
            'sql': 'sql.svg',
            'table': 'table.svg',
            'database': 'database.svg',
            'search': 'search.svg',
            'limit': 'limit.svg'
        }
        
        icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
        
        for key, filename in icon_files.items():
            icon_path = os.path.join(icons_dir, filename)
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.icons[key] = icon
            else:
                # Если иконка не найдена, создаем пустую иконку
                self.icons[key] = QIcon()
    
    def get_icon(self, name):
        """Получить иконку по имени"""
        return self.icons.get(name, QIcon())
    
    def set_button_icon(self, button, icon_name, text=""):
        """Установить иконку на кнопку"""
        icon = self.get_icon(icon_name)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(self.icon_size)
        if text:
            button.setText(text)

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Создаем градиентный фон
        splash_image = QPixmap(500, 300)
        splash_image.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(splash_image)
        
        # Черный градиент
        gradient = QLinearGradient(0, 0, 500, 300)
        gradient.setColorAt(0.0, QColor(10, 10, 10))
        gradient.setColorAt(0.5, QColor(30, 30, 30))
        gradient.setColorAt(1.0, QColor(20, 20, 20))
        
        painter.fillRect(0, 0, 500, 300, gradient)
        
        # Рисуем рамку
        pen = QPen(QColor(100, 100, 100))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(1, 1, 498, 298)
        
        painter.end()
        
        super().__init__(splash_image)
        
        # Логотип
        self.logo_label = QLabel(self)
        self.logo_label.setGeometry(150, 50, 200, 60)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_font = QFont()
        logo_font.setPointSize(24)
        logo_font.setBold(True)
        logo_font.setFamily("Segoe UI")
        self.logo_label.setFont(logo_font)
        self.logo_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                background: transparent;
            }
        """)
        self.logo_label.setText("SQLite Viewer")
        
        # Подзаголовок
        self.sub_label = QLabel(self)
        self.sub_label.setGeometry(150, 100, 200, 30)
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_font = QFont()
        sub_font.setPointSize(10)
        sub_font.setFamily("Segoe UI")
        self.sub_label.setFont(sub_font)
        self.sub_label.setStyleSheet("color: #808080;")
        self.sub_label.setText("Professional Database Tool")
        
        # Прогресс бар
        self.progress = QProgressBar(self)
        self.progress.setGeometry(100, 180, 300, 4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #333333;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #808080;
                border-radius: 2px;
            }
        """)
        
        # Статус
        self.status_label = QLabel(self)
        self.status_label.setGeometry(100, 190, 300, 20)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #808080; font-size: 9pt;")
        self.status_label.setText("Загрузка компонентов...")

class SQLiteEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.import_export = ImportExportManager()
        self.icon_manager = IconManager()
        self.init_ui()
        self.show_splash()
    
    def show_splash(self):
        self.splash = SplashScreen()
        self.splash.show()
        
        stages = [
            "Инициализация интерфейса...",
            "Загрузка модулей...",
            "Настройка базы данных...",
            "Подготовка инструментов...",
            "Завершение загрузки..."
        ]
        
        for i, stage in enumerate(stages):
            self.splash.progress.setValue((i + 1) * 20)
            self.splash.status_label.setText(stage)
            QApplication.processEvents()
            QThread.msleep(300)
        
        self.splash.finish(self)
        self.show()
    
    def init_ui(self):
        self.setWindowTitle("SQLite Table Viewer")
        self.setGeometry(100, 100, 1400, 800)
        
        # Устанавливаем градиентный фон
        self.setStyleSheet(Styles.MAIN_WINDOW)
        
        # Центральный виджет с градиентом
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)
        
        # Создаем компоненты интерфейса
        self.create_menu()
        self.create_toolbar()
        
        # Основной сплиттер
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet(Styles.SPLITTER)
        
        # Левая панель (список таблиц)
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Правая панель (таблицы и SQL)
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        main_splitter.setSizes([300, 1100])
        main_layout.addWidget(main_splitter)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(Styles.STATUS_BAR)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
    
    def create_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(Styles.MENU_BAR)
        
        # Файл
        file_menu = menubar.addMenu("Файл")
        
        open_action = QAction(self.icon_manager.get_icon('open'), "Открыть базу данных", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_database)
        file_menu.addAction(open_action)
        
        new_action = QAction(self.icon_manager.get_icon('new'), "Создать базу данных", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.create_database)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        close_action = QAction(self.icon_manager.get_icon('database'), "Закрыть базу данных", self)
        close_action.triggered.connect(self.close_database)
        file_menu.addAction(close_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Импорт/Экспорт
        import_menu = menubar.addMenu("Импорт")
        
        import_csv = QAction(self.icon_manager.get_icon('import'), "Импорт CSV", self)
        import_csv.triggered.connect(self.import_csv)
        import_menu.addAction(import_csv)
        
        import_json = QAction(self.icon_manager.get_icon('import'), "Импорт JSON", self)
        import_json.triggered.connect(self.import_json)
        import_menu.addAction(import_json)
        
        export_menu = menubar.addMenu("Экспорт")
        
        export_csv = QAction(self.icon_manager.get_icon('export'), "Экспорт CSV", self)
        export_csv.triggered.connect(self.export_csv)
        export_menu.addAction(export_csv)
        
        export_json = QAction(self.icon_manager.get_icon('export'), "Экспорт JSON", self)
        export_json.triggered.connect(self.export_json)
        export_menu.addAction(export_json)
        
        export_excel = QAction(self.icon_manager.get_icon('export'), "Экспорт Excel", self)
        export_excel.triggered.connect(self.export_excel)
        export_menu.addAction(export_excel)
        
        # Инструменты
        tools_menu = menubar.addMenu("Инструменты")
        
        backup_action = QAction(self.icon_manager.get_icon('database'), "Создать резервную копию", self)
        backup_action.triggered.connect(self.backup_database)
        tools_menu.addAction(backup_action)
        
        optimize_action = QAction(self.icon_manager.get_icon('refresh'), "Оптимизировать базу данных", self)
        optimize_action.triggered.connect(self.optimize_database)
        tools_menu.addAction(optimize_action)
        
        tools_menu.addSeparator()
        
        history_action = QAction(self.icon_manager.get_icon('sql'), "История запросов", self)
        history_action.triggered.connect(self.show_history)
        tools_menu.addAction(history_action)
        
        # Помощь
        help_menu = menubar.addMenu("Помощь")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(Styles.TOOLBAR)
        
        # Добавляем действия с иконками
        actions = [
            ('open', "Открыть", self.open_database),
            ('new', "Создать", self.create_database),
            ('import', "Импорт", self.import_csv),
            ('export', "Экспорт", self.export_csv),
            ('sql', "SQL", lambda: self.tabs.setCurrentIndex(1)),
            ('refresh', "Обновить", self.refresh_tables),
        ]
        
        for icon_name, text, func in actions:
            action = QAction(self.icon_manager.get_icon(icon_name), text, self)
            action.triggered.connect(func)
            toolbar.addAction(action)
            if icon_name != 'refresh':  # Добавляем разделители между всеми, кроме последнего
                toolbar.addSeparator()
        
        self.addToolBar(toolbar)
    
    def create_left_panel(self):
        panel = QWidget()
        panel.setStyleSheet(Styles.LEFT_PANEL)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок с иконкой
        title_layout = QHBoxLayout()
        db_icon_label = QLabel()
        db_icon_label.setPixmap(self.icon_manager.get_icon('database').pixmap(20, 20))
        title_layout.addWidget(db_icon_label)
        
        title_label = QLabel("БАЗА ДАННЫХ")
        title_label.setStyleSheet(Styles.PANEL_TITLE)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Информация о БД
        self.db_info_frame = QFrame()
        self.db_info_frame.setStyleSheet(Styles.INFO_FRAME)
        db_info_layout = QVBoxLayout()
        db_info_layout.setContentsMargins(10, 10, 10, 10)
        
        self.db_name_label = QLabel("Нет открытой БД")
        self.db_name_label.setStyleSheet("color: #808080; font-weight: bold;")
        db_info_layout.addWidget(self.db_name_label)
        
        self.db_size_label = QLabel("")
        self.db_size_label.setStyleSheet("color: #606060; font-size: 9pt;")
        db_info_layout.addWidget(self.db_size_label)
        
        self.db_info_frame.setLayout(db_info_layout)
        layout.addWidget(self.db_info_frame)
        
        # Список таблиц с иконкой
        tables_layout = QHBoxLayout()
        table_icon_label = QLabel()
        table_icon_label.setPixmap(self.icon_manager.get_icon('table').pixmap(20, 20))
        tables_layout.addWidget(table_icon_label)
        
        tables_label = QLabel("ТАБЛИЦЫ")
        tables_label.setStyleSheet(Styles.PANEL_TITLE)
        tables_layout.addWidget(tables_label)
        tables_layout.addStretch()
        layout.addLayout(tables_layout)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Имя таблицы")
        self.tree.setStyleSheet(Styles.TREE_WIDGET)
        self.tree.itemDoubleClicked.connect(self.load_table)
        layout.addWidget(self.tree)
        
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        panel = QWidget()
        panel.setStyleSheet(Styles.RIGHT_PANEL)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(Styles.TAB_WIDGET)
        
        # Вкладка просмотра данных
        from models import TableViewer
        self.data_viewer = TableViewer(self.icon_manager)
        self.tabs.addTab(self.data_viewer, self.icon_manager.get_icon('table'), "Просмотр данных")
        
        # Вкладка SQL запросов
        sql_widget = self.create_sql_tab()
        self.tabs.addTab(sql_widget, self.icon_manager.get_icon('sql'), "SQL запросы")
        
        layout.addWidget(self.tabs)
        panel.setLayout(layout)
        
        return panel
    
    def create_sql_tab(self):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Панель инструментов SQL
        sql_toolbar = QHBoxLayout()
        
        self.execute_btn = QPushButton(" Выполнить (F5)")
        self.icon_manager.set_button_icon(self.execute_btn, 'sql')
        self.execute_btn.setStyleSheet(Styles.SQL_BUTTON)
        self.execute_btn.clicked.connect(self.execute_query)
        sql_toolbar.addWidget(self.execute_btn)
        
        self.clear_btn = QPushButton(" Очистить")
        self.icon_manager.set_button_icon(self.clear_btn, 'refresh')
        self.clear_btn.setStyleSheet(Styles.SQL_BUTTON)
        self.clear_btn.clicked.connect(lambda: self.sql_input.clear())
        sql_toolbar.addWidget(self.clear_btn)
        
        sql_toolbar.addStretch()
        
        # SQL редактор
        self.sql_input = QTextEdit()
        self.sql_input.setPlaceholderText("Введите SQL запрос...")
        self.sql_input.setStyleSheet(Styles.SQL_EDITOR)
        
        from styles import SQLHighlighter
        self.highlighter = SQLHighlighter(self.sql_input.document())
        
        layout.addLayout(sql_toolbar)
        layout.addWidget(self.sql_input)
        
        widget.setLayout(layout)
        return widget
    
    def open_database(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Открыть базу данных", 
            "", 
            "SQLite files (*.db *.sqlite *.db3);;All files (*.*)"
        )
        
        if file_path and self.db_manager.connect(file_path):
            self.data_viewer.set_connection(self.db_manager.connection)
            self.load_tables()
            
            # Обновляем информацию о БД
            self.db_name_label.setText(os.path.basename(file_path))
            size_str = utils.format_size(os.path.getsize(file_path))
            self.db_size_label.setText(f"Размер: {size_str}")
            
            self.status_bar.showMessage(f"База данных загружена: {file_path}")
    
    def load_tables(self):
        self.tree.clear()
        tables = self.db_manager.get_tables()
        
        for table_name, count in tables:
            item = QTreeWidgetItem([f"{table_name}"])
            item.setData(0, Qt.ItemDataRole.UserRole, table_name)
            
            # Добавляем информацию о количестве записей
            count_label = QLabel(f"{count} зап.")
            count_label.setStyleSheet("color: #606060; padding-right: 10px;")
            self.tree.setItemWidget(item, 0, count_label)
            
            self.tree.addTopLevelItem(item)
    
    def load_table(self, item):
        table_name = item.data(0, Qt.ItemDataRole.UserRole)
        if table_name:
            self.data_viewer.load_table_data(table_name)
            self.tabs.setCurrentIndex(0)
            self.status_bar.showMessage(f"Загружена таблица {table_name}")
    
    def execute_query(self):
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        query = self.sql_input.toPlainText().strip()
        if not query:
            return
        
        success, result, columns = self.db_manager.execute_query(query)
        
        if success:
            if result is not None:  # SELECT запрос
                self.data_viewer.current_data = result
                self.data_viewer.current_headers = columns
                self.data_viewer.model.update_data(result, columns)
                self.data_viewer.table.resizeColumnsToContents()
                
                self.status_bar.showMessage(f"Запрос выполнен. Получено строк: {len(result)}")
                self.tabs.setCurrentIndex(0)
            else:
                self.status_bar.showMessage(f"Запрос выполнен. Таблицы обновлены.")
                self.load_tables()
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка выполнения запроса:\n{result}")
    
    def import_csv(self):
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Импорт CSV", "", "CSV files (*.csv)")
        if file_path:
            success, msg = self.import_export.import_csv(file_path, self.db_manager.connection)
            if success:
                self.load_tables()
                QMessageBox.information(self, "Успех", msg)
            else:
                QMessageBox.critical(self, "Ошибка", msg)
    
    def import_json(self):
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Импорт JSON", "", "JSON files (*.json)")
        if file_path:
            success, msg = self.import_export.import_json(file_path, self.db_manager.connection)
            if success:
                self.load_tables()
                QMessageBox.information(self, "Успех", msg)
            else:
                QMessageBox.critical(self, "Ошибка", msg)
    
    def export_csv(self):
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        tables = self.db_manager.get_table_names()
        if not tables:
            return
        
        table_name, ok = QInputDialog.getItem(self, "Экспорт", "Выберите таблицу:", tables, 0, False)
        if ok and table_name:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", 
                                                      f"{table_name}.csv", "CSV files (*.csv)")
            if file_path:
                success, msg = self.import_export.export_csv(table_name, file_path, self.db_manager.connection)
                if success:
                    QMessageBox.information(self, "Успех", msg)
                else:
                    QMessageBox.critical(self, "Ошибка", msg)
    
    def export_json(self):
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        tables = self.db_manager.get_table_names()
        if not tables:
            return
        
        table_name, ok = QInputDialog.getItem(self, "Экспорт", "Выберите таблицу:", tables, 0, False)
        if ok and table_name:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить JSON", 
                                                      f"{table_name}.json", "JSON files (*.json)")
            if file_path:
                success, msg = self.import_export.export_json(table_name, file_path, self.db_manager.connection)
                if success:
                    QMessageBox.information(self, "Успех", msg)
                else:
                    QMessageBox.critical(self, "Ошибка", msg)
    
    def export_excel(self):
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        tables = self.db_manager.get_table_names()
        if not tables:
            return
        
        table_name, ok = QInputDialog.getItem(self, "Экспорт", "Выберите таблицу:", tables, 0, False)
        if ok and table_name:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить Excel", 
                                                      f"{table_name}.xlsx", "Excel files (*.xlsx)")
            if file_path:
                success, msg = self.import_export.export_excel(table_name, file_path, self.db_manager.connection)
                if success:
                    QMessageBox.information(self, "Успех", msg)
                else:
                    QMessageBox.critical(self, "Ошибка", msg)
    
    def create_database(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Создать базу данных", 
                                                   "database.db", "SQLite files (*.db)")
        if file_path and self.db_manager.create_database(file_path):
            self.data_viewer.set_connection(self.db_manager.connection)
            self.db_name_label.setText(os.path.basename(file_path))
            self.db_size_label.setText("Размер: 0 Б")
            self.status_bar.showMessage(f"Создана база данных: {file_path}")
    
    def close_database(self):
        if self.db_manager.connection:
            self.db_manager.close()
            self.data_viewer.clear()
            self.tree.clear()
            self.db_name_label.setText("Нет открытой БД")
            self.db_size_label.setText("")
            self.status_bar.showMessage("База данных закрыта")
    
    def refresh_tables(self):
        self.load_tables()
        self.status_bar.showMessage("Список таблиц обновлен")
    
    def backup_database(self):
        if not self.db_manager.current_db:
            QMessageBox.warning(self, "Предупреждение", "Нет открытой базы данных!")
            return
        
        success, msg = self.db_manager.backup_database()
        if success:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)
    
    def optimize_database(self):
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Нет открытой базы данных!")
            return
        
        success, msg = self.db_manager.optimize_database()
        if success:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)
    
    def show_history(self):
        from dialogs import HistoryDialog
        dialog = HistoryDialog(self.db_manager.query_history, self)
        dialog.exec()
    
    def show_about(self):
        QMessageBox.about(self, "О программе", 
                         """<h2 style='color: #e0e0e0;'>SQLite Table Viewer</h2>
                         <p style='color: #808080;'>Версия: 2.0</p>
                         <p style='color: #a0a0a0;'>Профессиональный инструмент для работы с SQLite базами данных</p>
                         <hr style='border: 1px solid #404040;'>
                         <p style='color: #606060;'>Разработано с использованием PyQt6</p>""")
    
    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Устанавливаем темную палитру
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.Button, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(100, 100, 100))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(80, 80, 80))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)
    
    window = SQLiteEditor()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()