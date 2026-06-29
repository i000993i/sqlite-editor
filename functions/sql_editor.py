from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from functions.logger import main_logger, db_logger
from typing import List, Dict, Optional
import json
from datetime import datetime

SQL_KEYWORDS = [
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN",
    "ORDER BY", "GROUP BY", "HAVING", "LIMIT", "OFFSET", "AS", "DISTINCT",
    "INSERT INTO", "VALUES", "UPDATE", "SET", "DELETE FROM",
    "CREATE TABLE", "ALTER TABLE", "DROP TABLE",
    "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN", "JOIN", "ON",
    "PRIMARY KEY", "FOREIGN KEY", "REFERENCES", "UNIQUE", "NOT NULL", "DEFAULT",
    "INTEGER", "TEXT", "REAL", "BLOB", "VARCHAR", "BOOLEAN",
    "COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "IFNULL", "NULLIF",
    "CASE", "WHEN", "THEN", "ELSE", "END", "CAST", "TYPEOF",
    "BEGIN", "COMMIT", "ROLLBACK", "TRANSACTION", "SAVEPOINT",
    "PRAGMA", "VACUUM", "ANALYZE", "EXPLAIN", "QUERY PLAN",
    "UNION", "UNION ALL", "EXCEPT", "INTERSECT",
    "ASC", "DESC", "NULLS FIRST", "NULLS LAST",
    "IF", "EXISTS", "GLOB", "REGEXP", "MATCH"
]

class SQLHighlighter(QSyntaxHighlighter):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.keywords = SQL_KEYWORDS
        
        # Форматирование
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569CD6"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))
        
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#D7BA7D"))
        
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#808080"))
        self.comment_format.setFontItalic(True)
        
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#DCDCAA"))
        
        self.rules = []
        
        for keyword in self.keywords:
            pattern = QRegularExpression(r"\b" + keyword + r"\b", QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.rules.append((pattern, self.keyword_format))
        
        pattern = QRegularExpression(r"'[^']*'")
        self.rules.append((pattern, self.string_format))
        
        pattern = QRegularExpression(r"\b\d+\b")
        self.rules.append((pattern, self.number_format))
        
        pattern = QRegularExpression(r"--[^\n]*")
        self.rules.append((pattern, self.comment_format))
        
        self.function_pattern = QRegularExpression(r"\b(\w+)\s*\(")
    
    def highlightBlock(self, text):
        for pattern, format in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        
        function_iterator = self.function_pattern.globalMatch(text)
        while function_iterator.hasNext():
            match = function_iterator.next()
            self.setFormat(match.capturedStart(1), match.capturedLength(1), self.function_format)


class SQLAutoComplete:
    def __init__(self, text_edit: QTextEdit):
        self.text_edit = text_edit
        self.completer = None
        self.schema_data = {}
        self._setup_completer()
    
    def _setup_completer(self):
        keywords = list(set(kw + "()" if kw in ("COUNT","SUM","AVG","MIN","MAX") else kw for kw in SQL_KEYWORDS))
    
        self.completer = QCompleter(keywords)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setWidget(self.text_edit)
        self.completer.activated.connect(self._insert_completion)
        
        self.completer.popup().setStyleSheet("""
            QListView {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #303030;
                selection-background-color: #404040;
            }
            QListView::item {
                padding: 5px;
            }
            QListView::item:selected {
                background-color: #404040;
            }
        """)
    
    def _insert_completion(self, completion: str):
        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.text_edit.setTextCursor(cursor)
    
    def load_schema(self, connection):
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.schema_data = {'tables': {}, 'columns': {}}
            
            items = []
            for table in tables:
                cursor.execute(f"PRAGMA table_info(\"{table}\")")
                columns = [row[1] for row in cursor.fetchall()]
                
                self.schema_data['tables'][table] = True
                self.schema_data['columns'][table] = columns
                
                items.append(table)
                items.extend(f"{table}.{col}" for col in columns)
            
            self.completer.model().setStringList(items)
            main_logger.info(f"Автодополнение загружено: {len(tables)} таблиц")
            
        except Exception as e:
            main_logger.error(f"Ошибка загрузки схемы для автодополнения: {e}")
    
    def show_completions(self):
        if self.completer:
            cursor_rect = self.text_edit.cursorRect()
            cursor_rect.setWidth(self.completer.popup().sizeHintForColumn(0) + 20)
            self.completer.complete(cursor_rect)


class QueryHistory:
    """История SQL запросов"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.history: List[Dict] = []
        self._load_history()
    
    def _history_file(self) -> str:
        return "logs/query_history.json"
    
    def _load_history(self):
        """Загрузить историю из файла"""
        import os
        if os.path.exists(self._history_file()):
            try:
                with open(self._history_file(), 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []
    
    def _save_history(self):
        """Сохранить историю в файл"""
        import os
        from pathlib import Path
        Path("logs").mkdir(exist_ok=True)
        
        try:
            with open(self._history_file(), 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            main_logger.error(f"Ошибка сохранения истории: {e}")
    
    def add(self, query: str, success: bool = True, result_count: int = 0):
        """Добавить запрос в историю"""
        entry = {
            'query': query.strip(),
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'result_count': result_count
        }
        
        # Добавить в начало
        self.history.insert(0, entry)
        
        # Ограничить размер
        if len(self.history) > self.max_size:
            self.history = self.history[:self.max_size]
        
        self._save_history()
    
    def get_all(self) -> List[Dict]:
        """Получить всю историю"""
        return self.history
    
    def search(self, pattern: str) -> List[Dict]:
        """Поиск по истории"""
        pattern_lower = pattern.lower()
        return [
            entry for entry in self.history
            if pattern_lower in entry['query'].lower()
        ]
    
    def clear(self):
        """Очистить историю"""
        self.history = []
        self._save_history()


class ExplainQueryDialog(QDialog):
    """Диалог для отображения EXPLAIN QUERY PLAN"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("EXPLAIN QUERY PLAN")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        
        # Текстовый редактор для вывода
        self.text_editor = QTextEdit()
        font = QFont("Consolas", 10)
        self.text_editor.setFont(font)
        self.text_editor.setReadOnly(True)
        self.text_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #303030;
                padding: 10px;
            }
        """)
        
        layout.addWidget(QLabel("План выполнения запроса:"))
        layout.addWidget(self.text_editor)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Сохранить в файл")
        save_btn.clicked.connect(self.save_to_file)
        btn_layout.addWidget(save_btn)
        
        copy_btn = QPushButton("Копировать")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def set_plan(self, plan_text: str):
        """Установить текст плана"""
        self.text_editor.setText(plan_text)
    
    def save_to_file(self):
        """Сохранить в файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить план запроса", "", "Text files (*.txt);;All files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_editor.toPlainText())
                QMessageBox.information(self, "Успех", f"План сохранён в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")
    
    def copy_to_clipboard(self):
        """Копировать в буфер"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_editor.toPlainText())


class SQLQueryPanel(QWidget):
    """Панель SQL редактора с подсветкой, автодополнением и историей"""
    
    # Сигналы
    query_executed = pyqtSignal(str, bool, int)  # query, success, result_count
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_connection = None
        self.async_manager = None
        self.history = QueryHistory()
        self.history_dialog = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        # Кнопка выполнения
        self.execute_btn = QPushButton("▶ Выполнить (F5)")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D5A2D;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D7A3D;
            }
            QPushButton:pressed {
                background-color: #1D4A1D;
            }
        """)
        self.execute_btn.clicked.connect(self.execute_query)
        toolbar.addWidget(self.execute_btn)
        
        # Кнопка Explain
        self.explain_btn = QPushButton("📋 EXPLAIN QUERY PLAN")
        self.explain_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D5A;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #3D3D7A;
            }
        """)
        self.explain_btn.clicked.connect(self.explain_query)
        toolbar.addWidget(self.explain_btn)
        
        # Кнопка автодополнения
        self.auto_complete_btn = QPushButton("💡 Автодополнение (Ctrl+Space)")
        self.auto_complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D5A5A;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #3D7A7A;
            }
        """)
        self.auto_complete_btn.clicked.connect(self.show_auto_complete)
        toolbar.addWidget(self.auto_complete_btn)
        
        # Кнопка истории
        self.history_btn = QPushButton("📜 История")
        self.history_btn.setStyleSheet("""
            QPushButton {
                background-color: #5A5A2D;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #7A7A3D;
            }
        """)
        self.history_btn.clicked.connect(self.show_history)
        toolbar.addWidget(self.history_btn)
        
        # Кнопка очистки
        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #5A2D2D;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #7A3D3D;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_editor)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # SQL редактор
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Введите SQL запрос...\n\nF5 или Ctrl+Enter - выполнить\nCtrl+Space - автодополнение")
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #303030;
                border-radius: 4px;
                padding: 10px;
                font-family: Consolas;
                font-size: 11pt;
            }
            QTextEdit:focus {
                border: 1px solid #569CD6;
            }
        """)
        
        # Шрифт
        font = QFont("Consolas", 11)
        self.editor.setFont(font)
        
        # Подсветка синтаксиса
        self.highlighter = SQLHighlighter(self.editor.document())
        
        # Автодополнение
        self.auto_complete = SQLAutoComplete(self.editor)
        
        # Горячие клавиши
        self.editor.installEventFilter(self)
        
        layout.addWidget(self.editor)
        
        # Диалог Explain
        self.explain_dialog = ExplainQueryDialog(self)
        
        self.setLayout(layout)
    
    def eventFilter(self, obj, event):
        """Обработка событий для горячих клавиш"""
        if event.type() == QEvent.Type.KeyPress:
            # F5 для выполнения
            if event.key() == Qt.Key.Key_F5:
                self.execute_query()
                return True
            
            # Ctrl+Enter для выполнения
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Return:
                self.execute_query()
                return True
            
            # Ctrl+Space для автодополнения
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Space:
                self.show_auto_complete()
                return True
        
        return super().eventFilter(obj, event)
    
    def set_connection(self, connection):
        """Установить подключение к БД"""
        self.db_connection = connection
        if connection:
            self.auto_complete.load_schema(connection)
    
    def execute_query(self):
        """Отправить запрос на выполнение (выполняется в главном окне асинхронно)"""
        query = self.editor.toPlainText().strip()
        
        if not query:
            return
        
        if not self.db_connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        self.query_executed.emit(query, True, 0)
    
    def set_async_manager(self, async_manager):
        """Установить менеджер асинхронных операций"""
        self.async_manager = async_manager
    
    def explain_query(self):
        """Показать EXPLAIN QUERY PLAN"""
        query = self.editor.toPlainText().strip()
        
        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите SQL запрос!")
            return
        
        if not self.db_connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте базу данных!")
            return
        
        try:
            cursor = self.db_connection.cursor()
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor.execute(explain_query)
            result = cursor.fetchall()
            
            # Форматирование результата
            plan_text = "План выполнения запроса:\n" + "=" * 50 + "\n\n"
            
            for row in result:
                if len(row) >= 4:
                    # id, parent, notused, detail
                    detail = row[3] if row[3] else ""
                    plan_text += f"  → {detail}\n"
                else:
                    plan_text += f"  → {row}\n"
            
            # Если план пустой
            if not result:
                plan_text += "  (Нет данных о плане)\n"
            
            plan_text += "\n" + "=" * 50
            plan_text += "\n\nСоветы по оптимизации:"
            plan_text += "\n- Используйте INDEX для больших таблиц"
            plan_text += "\n- Избегайте SELECT *"
            plan_text += "\n- Используйте WHERE для фильтрации"
            
            self.explain_dialog.set_plan(plan_text)
            self.explain_dialog.show()
            
            db_logger.info("EXPLAIN QUERY PLAN выполнен")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка выполнения EXPLAIN:\n{e}")
            db_logger.error(f"Ошибка EXPLAIN QUERY PLAN: {e}")
    
    def show_auto_complete(self):
        """Показать автодополнение"""
        self.auto_complete.show_completions()
    
    def show_history(self):
        """Показать диалог истории"""
        if not self.history_dialog:
            self.history_dialog = QueryHistoryDialog(self.history, self)
            self.history_dialog.query_selected.connect(self.load_query)
        
        self.history_dialog.show()
        self.history_dialog.raise_()
    
    def load_query(self, query: str):
        """Загрузить запрос из истории в редактор"""
        self.editor.setText(query)
    
    def clear_editor(self):
        """Очистить редактор"""
        self.editor.clear()


class QueryHistoryDialog(QDialog):
    """Диалог истории запросов"""
    
    query_selected = pyqtSignal(str)
    
    def __init__(self, history: QueryHistory, parent=None):
        super().__init__(parent)
        self.history = history
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("История запросов")
        self.setGeometry(200, 200, 900, 600)
        
        layout = QVBoxLayout()
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по истории...")
        self.search_input.textChanged.connect(self.filter_history)
        search_layout.addWidget(self.search_input)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # Список истории
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_selected)
        layout.addWidget(self.list_widget)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh_list)
        btn_layout.addWidget(refresh_btn)
        
        clear_btn = QPushButton("Очистить историю")
        clear_btn.clicked.connect(self.clear_history)
        btn_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Заполнить список
        self.refresh_list()
    
    def refresh_list(self):
        """Обновить список истории"""
        self.list_widget.clear()
        
        for entry in self.history.get_all():
            query_preview = entry['query'][:100] + "..." if len(entry['query']) > 100 else entry['query']
            
            # Форматирование
            timestamp = entry['timestamp'][:19].replace('T', ' ')
            status = "✓" if entry['success'] else "✗"
            count = entry['result_count']
            
            item_text = f"[{status}] {timestamp} | {count} строк | {query_preview}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, entry['query'])
            
            # Цвет в зависимости от статуса
            if entry['success']:
                item.setForeground(QColor("#90EE90"))
            else:
                item.setForeground(QColor("#FF6B6B"))
            
            self.list_widget.addItem(item)
    
    def filter_history(self, pattern: str):
        """Фильтровать историю"""
        self.list_widget.clear()
        
        if not pattern:
            self.refresh_list()
            return

        results = self.history.search(pattern)
        
        for entry in results:
            query_preview = entry['query'][:100] + "..." if len(entry['query']) > 100 else entry['query']
            
            timestamp = entry['timestamp'][:19].replace('T', ' ')
            status = "✓" if entry['success'] else "✗"
            count = entry['result_count']
            
            item_text = f"[{status}] {timestamp} | {count} строк | {query_preview}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, entry['query'])
            
            if entry['success']:
                item.setForeground(QColor("#90EE90"))
            else:
                item.setForeground(QColor("#FF6B6B"))
            
            self.list_widget.addItem(item)
    
    def on_item_selected(self, item: QListWidgetItem):
        """Выбор элемента истории"""
        query = item.data(Qt.ItemDataRole.UserRole)
        self.query_selected.emit(query)
        self.accept()
    
    def clear_history(self):
        """Очистить историю"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы действительно хотите очистить всю историю запросов?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.refresh_list()
