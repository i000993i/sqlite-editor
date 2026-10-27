import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QLabel, QFrame,
    QStatusBar, QTabWidget, QToolBar, QMenuBar, QFileDialog,
    QMessageBox, QInputDialog, QSplashScreen, QProgressBar,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QPen, QFont, QPalette, QAction

from functions.paths import logs_dir, icons_dir
from functions.logger import main_logger
from functions.styles import Styles
from functions.database import DatabaseManager
from functions import utils
from functions.import_export import ImportExportManager
from functions.table_viewer_virtual import TableViewerVirtual, ProgressOverlay
from functions.async_manager import AsyncManager
from functions.sql_editor import SQLQueryPanel
from functions.table_designer import TableDesigner
from functions.data_visualizer import DataVisualizer


class IconManager:
    ICON_FILES = {
        "open": "open.svg", "new": "new.svg", "refresh": "refresh.svg",
        "import": "import.svg", "export": "export.svg", "sql": "sql.svg",
        "table": "table.svg", "database": "database.svg",
        "search": "search.svg", "limit": "limit.svg",
    }

    def __init__(self):
        self.icons = {}
        self.icon_size = QSize(20, 20)
        self._load_icons()

    def _load_icons(self):
        base = icons_dir()
        for key, filename in self.ICON_FILES.items():
            path = base / filename
            if path.exists():
                self.icons[key] = QIcon(str(path))
            else:
                main_logger.warning(f"Иконка не найдена: {path}")
                self.icons[key] = QIcon()

    def get_icon(self, name):
        return self.icons.get(name, QIcon())

    def set_button_icon(self, button, icon_name, text=""):
        icon = self.get_icon(icon_name)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(self.icon_size)
        if text:
            button.setText(text)


class SplashScreen(QSplashScreen):

    def __init__(self):
        screen = QApplication.primaryScreen()
        dpi = screen.logicalDotsPerInch() if screen else 96.0
        scale = dpi / 96.0
        w, h = int(600 * scale), int(350 * scale)
        margin = max(1, int(scale))

        img = QPixmap(w, h)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(10, 10, 10))
        grad.setColorAt(0.5, QColor(30, 30, 30))
        grad.setColorAt(1.0, QColor(20, 20, 20))
        p.fillRect(0, 0, w, h, grad)
        pen = QPen(QColor(100, 100, 100)); pen.setWidth(margin * 2)
        p.setPen(pen); p.drawRect(margin, margin, w - margin * 2, h - margin * 2)
        p.end()

        super().__init__(img)

        def s(v):
            return int(v * scale)

        self.logo_label = QLabel(self)
        self.logo_label.setGeometry(s(50), s(50), s(500), s(70))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont("Segoe UI"); f.setPointSize(max(1, int(26 * scale))); f.setBold(True)
        self.logo_label.setFont(f)
        self.logo_label.setStyleSheet("QLabel{color:#e0e0e0;background:transparent;}")
        self.logo_label.setText("SQLite Table Viewer")

        self.sub_label = QLabel(self)
        self.sub_label.setGeometry(s(150), s(120), s(300), s(30))
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f2 = QFont("Segoe UI"); f2.setPointSize(max(1, int(10 * scale)))
        self.sub_label.setFont(f2)
        self.sub_label.setStyleSheet("color:#808080;")
        self.sub_label.setText("Professional Database Tool")

        self.progress = QProgressBar(self)
        self.progress.setGeometry(s(100), s(200), s(400), max(1, s(4)))
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar{border:none;background-color:#333;border-radius:2px;}"
            "QProgressBar::chunk{background-color:#808080;border-radius:2px;}")

        self.status_label = QLabel(self)
        self.status_label.setGeometry(s(100), s(210), s(400), s(25))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color:#808080;font-size:9pt;")
        self.status_label.setText("Загрузка компонентов...")


class SQLiteEditor(QMainWindow):

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.import_export = ImportExportManager()
        self.icon_manager = IconManager()
        self.async_manager = AsyncManager()
        self._current_table_for_visualizer = None
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
            "Завершение загрузки...",
        ]
        for i, stage in enumerate(stages):
            self.splash.progress.setValue((i + 1) * 20)
            self.splash.status_label.setText(stage)
            QApplication.processEvents()

        self.splash.finish(self)
        self.show()

    # ---------------- UI ----------------

    def init_ui(self):
        self.setWindowTitle("SQLite Table Viewer")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(Styles.MAIN_WINDOW)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central.setLayout(main_layout)

        self.create_menu()
        self.create_toolbar()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(Styles.SPLITTER)
        splitter.addWidget(self.create_left_panel())
        splitter.addWidget(self.create_right_panel())
        splitter.setSizes([300, 1100])
        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(Styles.STATUS_BAR)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

        self.progress_overlay = ProgressOverlay(self)
        self.progress_overlay.set_cancel_callback(self.cancel_operation)

    def cancel_operation(self):
        self.async_manager.cancel_current()
        self.progress_overlay.hide_blocking()

    def create_menu(self):
        mb = self.menuBar()
        mb.setStyleSheet(Styles.MENU_BAR)

        # Файл
        fm = mb.addMenu("Файл")
        a = QAction(self.icon_manager.get_icon("open"), "Открыть базу данных", self)
        a.setShortcut("Ctrl+O"); a.triggered.connect(self.open_database)
        fm.addAction(a)

        a = QAction(self.icon_manager.get_icon("new"), "Создать базу данных", self)
        a.setShortcut("Ctrl+N"); a.triggered.connect(self.create_database)
        fm.addAction(a)
        fm.addSeparator()

        a = QAction(self.icon_manager.get_icon("database"), "Закрыть базу данных", self)
        a.triggered.connect(self.close_database)
        fm.addAction(a)
        fm.addSeparator()

        a = QAction("Выход", self); a.setShortcut("Ctrl+Q")
        a.triggered.connect(self.close); fm.addAction(a)

        # Импорт
        im = mb.addMenu("Импорт")
        a = QAction(self.icon_manager.get_icon("import"), "Импорт CSV", self)
        a.triggered.connect(self.import_csv); im.addAction(a)
        a = QAction(self.icon_manager.get_icon("import"), "Импорт JSON", self)
        a.triggered.connect(self.import_json); im.addAction(a)

        # Экспорт
        em = mb.addMenu("Экспорт")
        for label, slot in (
            ("Экспорт CSV", self.export_csv),
            ("Экспорт JSON", self.export_json),
            ("Экспорт Excel", self.export_excel),
            ("Экспорт PDF", self.export_pdf),
        ):
            a = QAction(self.icon_manager.get_icon("export"), label, self)
            a.triggered.connect(slot); em.addAction(a)

        # Инструменты
        tm = mb.addMenu("Инструменты")
        a = QAction(self.icon_manager.get_icon("database"),
                    "Создать резервную копию", self)
        a.triggered.connect(self.backup_database); tm.addAction(a)
        a = QAction(self.icon_manager.get_icon("refresh"),
                    "Оптимизировать базу данных", self)
        a.triggered.connect(self.optimize_database); tm.addAction(a)
        tm.addSeparator()
        a = QAction(self.icon_manager.get_icon("sql"), "История запросов", self)
        a.triggered.connect(self.show_history); tm.addAction(a)

        # Помощь
        hm = mb.addMenu("Помощь")
        a = QAction("О программе", self); a.triggered.connect(self.show_about)
        hm.addAction(a)

    def create_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        tb.setStyleSheet(Styles.TOOLBAR)
        groups = [
            [("open", "Открыть", self.open_database),
             ("new", "Создать", self.create_database)],
            [("import", "Импорт", self.import_csv),
             ("export", "Экспорт", self.export_csv)],
            [("sql", "SQL", lambda: self.tabs.setCurrentIndex(1)),
             ("refresh", "Обновить", self.refresh_tables)],
            [("table", "Графики", lambda: self.tabs.setCurrentIndex(3))],
        ]
        for gi, group in enumerate(groups):
            if gi > 0:
                tb.addSeparator()
            for icon, text, func in group:
                a = QAction(self.icon_manager.get_icon(icon), text, self)
                a.triggered.connect(func)
                tb.addAction(a)
        self.addToolBar(tb)

    def create_left_panel(self):
        panel = QWidget()
        panel.setStyleSheet(Styles.LEFT_PANEL)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(self.icon_manager.get_icon("database").pixmap(20, 20))
        title.addWidget(ic)
        lbl = QLabel("БАЗА ДАННЫХ")
        lbl.setStyleSheet(Styles.PANEL_TITLE)
        title.addWidget(lbl); title.addStretch()
        layout.addLayout(title)

        self.db_info_frame = QFrame()
        self.db_info_frame.setStyleSheet(Styles.INFO_FRAME)
        bl = QVBoxLayout(self.db_info_frame)
        bl.setContentsMargins(10, 10, 10, 10)
        self.db_name_label = QLabel("Нет открытой БД")
        self.db_name_label.setStyleSheet("color:#808080;font-weight:bold;")
        bl.addWidget(self.db_name_label)
        self.db_size_label = QLabel("")
        self.db_size_label.setStyleSheet("color:#606060;font-size:9pt;")
        bl.addWidget(self.db_size_label)
        layout.addWidget(self.db_info_frame)

        tl = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(self.icon_manager.get_icon("table").pixmap(20, 20))
        tl.addWidget(ic)
        lbl = QLabel("ТАБЛИЦЫ")
        lbl.setStyleSheet(Styles.PANEL_TITLE)
        tl.addWidget(lbl); tl.addStretch()
        layout.addLayout(tl)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Имя таблицы")
        self.tree.setStyleSheet(Styles.TREE_WIDGET)
        self.tree.itemDoubleClicked.connect(self.load_table)
        layout.addWidget(self.tree)
        return panel

    def create_right_panel(self):
        panel = QWidget()
        panel.setStyleSheet(Styles.RIGHT_PANEL)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(Styles.TAB_WIDGET)

        self.data_viewer = TableViewerVirtual(self.icon_manager)
        self.tabs.addTab(self.data_viewer,
                         self.icon_manager.get_icon("table"), "Просмотр данных")

        self.tabs.addTab(self._create_sql_tab(),
                         self.icon_manager.get_icon("sql"), "SQL запросы")

        self.table_designer = TableDesigner()
        self.tabs.addTab(self.table_designer,
                         self.icon_manager.get_icon("table"), "Конструктор таблиц")

        self.data_visualizer = DataVisualizer()
        self.tabs.addTab(self.data_visualizer,
                         self.icon_manager.get_icon("table"), "Графики")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)
        return panel

    def _create_sql_tab(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        self.sql_panel = SQLQueryPanel()
        self.sql_panel.set_async_manager(self.async_manager)
        self.sql_panel.query_executed.connect(self.on_sql_query_executed)
        layout.addWidget(self.sql_panel)
        return w

    # ---------------- DB ---------------

    def _bind_db_manager(self):
        self.data_viewer.set_connection(self.db_manager)
        self.data_viewer.schema_cache.load_full_schema(self.db_manager.connection)
        self.sql_panel.set_connection(self.db_manager.connection)
        self.table_designer.set_connection(self.db_manager)
        self.data_visualizer.set_db_manager(self.db_manager)
        self.async_manager.set_db_connection(self.db_manager.connection)

    def open_database(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть базу данных", "",
            "SQLite files (*.db *.sqlite *.db3);;All files (*.*)")
        if not path:
            return
        main_logger.info(f"Открытие БД: {path}")
        if self.db_manager.connect(path):
            self._bind_db_manager()
            self.load_tables()
            self.db_name_label.setText(os.path.basename(path))
            self.db_size_label.setText(
                f"Размер: {utils.format_size(os.path.getsize(path))}")
            self.status_bar.showMessage(f"База данных загружена: {path}")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось открыть базу данных")

    def create_database(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Создать базу данных", "database.db", "SQLite files (*.db)")
        if not path:
            return
        if self.db_manager.create_database(path):
            self._bind_db_manager()
            self.load_tables()
            self.db_name_label.setText(os.path.basename(path))
            self.db_size_label.setText("Размер: 0 Б")
            self.status_bar.showMessage(f"Создана база данных: {path}")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось создать базу данных")

    def close_database(self):
        if self.db_manager.connection:
            main_logger.info(f"Закрытие БД: {self.db_manager.current_db}")
            self.async_manager.set_db_connection(None)
            self.db_manager.close()
            self.data_viewer.clear()
            self.tree.clear()
            self.sql_panel.set_connection(None)
            self.table_designer.set_connection(None)
            self.data_visualizer.set_db_manager(None)
            self.db_name_label.setText("Нет открытой БД")
            self.db_size_label.setText("")
            self.status_bar.showMessage("База данных закрыта")

    def load_tables(self):
        self.tree.clear()
        tables = (self.data_viewer.schema_cache.get_tables()
                  if self.data_viewer.schema_cache.is_valid()
                  else self.db_manager.get_tables())
        for name, count in tables:
            item = QTreeWidgetItem([name])
            item.setData(0, Qt.ItemDataRole.UserRole, name)
            lbl = QLabel(f"{count} зап.")
            lbl.setStyleSheet("color:#606060;padding-right:10px;")
            self.tree.setItemWidget(item, 0, lbl)
            self.tree.addTopLevelItem(item)

    def load_table(self, item):
        name = item.data(0, Qt.ItemDataRole.UserRole)
        if name:
            self.data_viewer.load_table_data(name)
            self.tabs.setCurrentIndex(0)
            self._current_table_for_visualizer = name
            self.data_visualizer.set_current_table(name)
            self.status_bar.showMessage(f"Загружена таблица {name}")

    # ---------------- SQL ----------------

    def on_sql_query_executed(self, query: str, success: bool, result_count: int):
        if not success:
            return
        is_select = query.lstrip().upper().startswith(("SELECT", "PRAGMA", "EXPLAIN"))
        self.progress_overlay.show_blocking("Выполнение запроса...")

        def execute_task():
            return self.db_manager.execute_query(query)

        def on_finished(result):
            ok, data, columns = result
            if not ok:
                self.sql_panel.history.add(query, success=False, result_count=0)
                QMessageBox.critical(self, "Ошибка", f"Ошибка запроса:\n{data}")
                return
            if is_select:
                rows = data or []
                self.data_viewer.model.set_data(rows, columns or [], len(rows))
                self.data_viewer.edit_mode_btn.setChecked(False)
                self.data_viewer.edit_mode_btn.setEnabled(False)
                self.sql_panel.history.add(query, success=True, result_count=len(rows))
                self.status_bar.showMessage(f"Запрос выполнен. Строк: {len(rows)}")
                self.tabs.setCurrentIndex(0)
            else:
                self.sql_panel.history.add(query, success=True, result_count=0)
                self.data_viewer.schema_cache.clear()
                self.data_viewer.edit_mode_btn.setEnabled(True)
                self.sql_panel.set_connection(self.db_manager.connection)
                self.load_tables()
                self.status_bar.showMessage("Запрос выполнен. Таблицы обновлены.")

        def on_error(msg):
            self.sql_panel.history.add(query, success=False, result_count=0)
            QMessageBox.critical(self, "Ошибка", f"Ошибка запроса:\n{msg}")

        worker = self.async_manager.execute_async(execute_task, on_finished, on_error)
        if worker:
            worker.finished.connect(
                self.progress_overlay.hide_blocking,
                Qt.ConnectionType.SingleShotConnection,
            )
        else:
            self.progress_overlay.hide_blocking()

    def show_history(self):
        if hasattr(self, "sql_panel"):
            self.sql_panel.show_history()

    # ---------------- import / export ----------------

    def _need_db(self) -> bool:
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return False
        return True

    def import_csv(self):
        if not self._need_db():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Импорт CSV", "",
                                               "CSV files (*.csv)")
        if path:
            ok, msg = self.import_export.import_csv(path, self.db_manager.connection)
            if ok:
                self.data_viewer.schema_cache.clear()
                self.load_tables()
                QMessageBox.information(self, "Успех", msg)
            else:
                QMessageBox.critical(self, "Ошибка", msg)

    def import_json(self):
        if not self._need_db():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Импорт JSON", "",
                                               "JSON files (*.json)")
        if path:
            ok, msg = self.import_export.import_json(path, self.db_manager.connection)
            if ok:
                self.data_viewer.schema_cache.clear()
                self.load_tables()
                QMessageBox.information(self, "Успех", msg)
            else:
                QMessageBox.critical(self, "Ошибка", msg)

    def _export_generic(self, dialog_title, default_ext, ext_filter, func):
        if not self._need_db():
            return
        tables = self.db_manager.get_table_names()
        if not tables:
            return
        name, ok = QInputDialog.getItem(self, dialog_title, "Выберите таблицу:",
                                         tables, 0, False)
        if not (ok and name):
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить", f"{name}.{default_ext}", ext_filter)
        if not path:
            return
        success, msg = func(name, path, self.db_manager.connection)
        if success:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)

    def export_csv(self):
        self._export_generic("Экспорт CSV", "csv", "CSV files (*.csv)",
                              self.import_export.export_csv)

    def export_json(self):
        self._export_generic("Экспорт JSON", "json", "JSON files (*.json)",
                              self.import_export.export_json)

    def export_excel(self):
        self._export_generic("Экспорт Excel", "xlsx", "Excel files (*.xlsx)",
                              self.import_export.export_excel)

    def export_pdf(self):
        if not self._need_db():
            return
        tables = self.db_manager.get_table_names()
        if not tables:
            return
        name, ok = QInputDialog.getItem(self, "Экспорт PDF", "Выберите таблицу:",
                                         tables, 0, False)
        if not (ok and name):
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить PDF", f"{name}.pdf", "PDF files (*.pdf)")
        if not path:
            return
        ok, msg = self.import_export.export_pdf(
            name, path, self.db_manager.connection, title=f"Экспорт: {name}")
        if ok:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)

    # ---------------- tools ----------------

    def refresh_tables(self):
        self.load_tables()
        if hasattr(self, "data_visualizer"):
            self.data_visualizer.refresh_tables()
        self.status_bar.showMessage("Список таблиц обновлён")

    def backup_database(self):
        if not self.db_manager.current_db:
            QMessageBox.warning(self, "Предупреждение", "Нет открытой БД!")
            return
        ok, msg = self.db_manager.backup_database()
        if ok:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)

    def optimize_database(self):
        if not self.db_manager.connection:
            QMessageBox.warning(self, "Предупреждение", "Нет подключения!")
            return
        ok, msg = self.db_manager.optimize_database()
        if ok:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)

    def show_about(self):
        QMessageBox.about(self, "О программе",
            "<h2 style='color:#e0e0e0;'>SQLite Table Viewer</h2>"
            "<p style='color:#808080;'>Версия 2.1 (Win10 / Linux)</p>"
            "<p style='color:#a0a0a0;'>PyQt6 · pandas · NumPy · matplotlib</p>")

    def _on_tab_changed(self, index):
        if index == 3 and self._current_table_for_visualizer:
            self.data_visualizer.auto_build(self._current_table_for_visualizer)

    def closeEvent(self, event):
        main_logger.info("Приложение закрывается")
        self.async_manager.cancel_current()
        self.db_manager.close()
        event.accept()


def main():
    logs_dir()                          # создаём папку логов
    main_logger.info("=" * 50)
    main_logger.info("Запуск SQLite Table Viewer")
    main_logger.info("=" * 50)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(20, 20, 20))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
    pal.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 30))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(224, 224, 224))
    pal.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
    pal.setColor(QPalette.ColorRole.Button, QColor(40, 40, 40))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
    pal.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    pal.setColor(QPalette.ColorRole.Link, QColor(100, 100, 100))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(80, 80, 80))
    pal.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(pal)

    w = SQLiteEditor()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()