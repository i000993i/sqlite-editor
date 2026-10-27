import json
from datetime import datetime
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
    QDialog, QFileDialog, QMessageBox, QCompleter, QListWidget,
    QListWidgetItem, QLineEdit, QApplication, QMenu,
)
from PyQt6.QtCore import Qt, QEvent, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QColor, QFont, QFontDatabase, QSyntaxHighlighter,
    QTextCharFormat, QTextCursor,
)

from functions.logger import main_logger, db_logger
from functions.paths import history_file

# ---------------- SQL keywords ----------------

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
    "IF", "EXISTS", "GLOB", "REGEXP", "MATCH",
]


def _monospace_font(size: int = 11) -> QFont:
    families = set(QFontDatabase.families())
    for name in ("JetBrains Mono", "Consolas", "DejaVu Sans Mono",
                 "Liberation Mono", "Menlo", "Monaco"):
        if name in families:
            return QFont(name, size)
    return QFont("monospace", size)


# ---------------- Highlighter ----------------

class SQLHighlighter(QSyntaxHighlighter):

    def __init__(self, parent=None):
        super().__init__(parent)

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
        for kw in SQL_KEYWORDS:
            pat = QRegularExpression(
                r"\b" + kw + r"\b",
                QRegularExpression.PatternOption.CaseInsensitiveOption,
            )
            self.rules.append((pat, self.keyword_format))

        self.rules.append((QRegularExpression(r"'[^']*'"), self.string_format))
        self.rules.append((QRegularExpression(r"\b\d+\b"), self.number_format))
        self.rules.append((QRegularExpression(r"--[^\n]*"), self.comment_format))

        self.function_pattern = QRegularExpression(r"\b(\w+)\s*\(")

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

        it = self.function_pattern.globalMatch(text)
        while it.hasNext():
            m = it.next()
            self.setFormat(m.capturedStart(1), m.capturedLength(1),
                           self.function_format)


# ---------------- Autocomplete ----------------

class SQLAutoComplete:

    def __init__(self, editor: QTextEdit):
        self.editor = editor
        self.completer = None
        self.schema_data = {}
        self._setup()

    def _setup(self):
        base = sorted({
            kw + ("()" if kw in ("COUNT", "SUM", "AVG", "MIN", "MAX") else "")
            for kw in SQL_KEYWORDS
        })
        self.completer = QCompleter(base)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setWidget(self.editor)
        self.completer.activated.connect(self._insert)
        self.completer.popup().setStyleSheet(
            "QListView{background:#1a1a1a;color:#e0e0e0;border:1px solid #303030;"
            "selection-background-color:#404040;}"
            "QListView::item{padding:5px;}")

    def _insert(self, text: str):
        cur = self.editor.textCursor()
        cur.select(QTextCursor.SelectionType.WordUnderCursor)
        cur.insertText(text)
        self.editor.setTextCursor(cur)

    def load_schema(self, connection):
        if not connection:
            return
        try:
            cur = connection.cursor()
            cur.execute("SELECT name FROM sqlite_master "
                        "WHERE type='table' ORDER BY name")
            tables = [r[0] for r in cur.fetchall()]
            items = []
            for t in tables:
                cur.execute(f'PRAGMA table_info("{t}")')
                cols = [r[1] for r in cur.fetchall()]
                items.append(t)
                items.extend(f"{t}.{c}" for c in cols)
            self.completer.model().setStringList(items)
            main_logger.info(f"Автодополнение: {len(tables)} таблиц")
        except Exception as e:
            main_logger.error(f"Автодополнение: {e}")

    def show_completions(self):
        if self.completer:
            rect = self.editor.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0) + 20)
            self.completer.complete(rect)


# ---------------- History ----------------

class QueryHistory:

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.history: List[Dict] = []
        self._load()

    def _load(self):
        path = history_file()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def _save(self):
        try:
            with open(history_file(), "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            main_logger.error(f"История: {e}")

    def add(self, query: str, success: bool = True, result_count: int = 0):
        self.history.insert(0, {
            "query": query.strip(),
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "result_count": result_count,
        })
        self.history = self.history[: self.max_size]
        self._save()

    def get_all(self):
        return self.history

    def search(self, pattern: str):
        p = pattern.lower()
        return [e for e in self.history if p in e["query"].lower()]

    def clear(self):
        self.history = []
        self._save()


# ---------------- Explain dialog ----------------

class ExplainQueryDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("План выполнения запроса (EXPLAIN QUERY PLAN)")
        self.setMinimumSize(700, 480)
        self.resize(800, 600)
        self.setStyleSheet(
            "QDialog{background:#1e1e1e;}"
            "QLabel{color:#c0c0c0;font-size:13px;}"
            "QPushButton{background:#2d2d2d;color:#e0e0e0;"
            "border:1px solid #303030;border-radius:4px;"
            "padding:6px 16px;font-size:12px;}"
            "QPushButton:hover{background:#3d3d3d;}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.text = QTextEdit()
        self.text.setFont(_monospace_font(10))
        self.text.setReadOnly(True)
        self.text.setStyleSheet(
            "QTextEdit{background:#151515;color:#D4D4D4;"
            "border:1px solid #303030;border-radius:4px;padding:10px;}")

        layout.addWidget(QLabel("План выполнения запроса:"))
        layout.addWidget(self.text, 1)

        btns = QHBoxLayout()
        sb = QPushButton("💾 Сохранить в файл")
        sb.clicked.connect(self._save)
        btns.addWidget(sb)

        cb = QPushButton("📋 Копировать")
        cb.clicked.connect(self._copy)
        btns.addWidget(cb)

        btns.addStretch()
        cl = QPushButton("Закрыть")
        cl.clicked.connect(self.accept)
        btns.addWidget(cl)
        layout.addLayout(btns)

    def set_plan(self, text: str):
        self.text.setText(text)

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить план", "", "Text (*.txt);;All (*.*)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _copy(self):
        QApplication.clipboard().setText(self.text.toPlainText())


# ---------------- Main SQL panel ----------------

class SQLQueryPanel(QWidget):

    query_executed = pyqtSignal(str, bool, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_connection = None
        self.async_manager = None
        self.history = QueryHistory()
        self.history_dialog = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()

        def _btn(text, color, hover, slot, tooltip=""):
            b = QPushButton(text)
            b.setToolTip(tooltip)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:{color};color:white;border:none;"
                f"border-radius:5px;padding:8px 15px;font-weight:bold;}}"
                f"QPushButton:hover{{background:{hover};}}")
            b.clicked.connect(slot)
            return b

        toolbar.addWidget(_btn("▶ Выполнить (F5)", "#2D5A2D", "#3D7A3D",
                               self.execute_query,
                               "Выполнить SQL (F5 / Ctrl+Enter)"))
        toolbar.addWidget(_btn("📊 План запроса", "#2D2D5A", "#3D3D7A",
                               self.explain_query,
                               "EXPLAIN QUERY PLAN — показать план выполнения"))
        toolbar.addWidget(_btn("💡 Подсказки (Ctrl+Space)", "#2D5A5A",
                               "#3D7A7A", self.show_auto_complete,
                               "Автодополнение SQL (Ctrl+Space)"))
        toolbar.addWidget(_btn("📜 История", "#5A5A2D", "#7A7A3D",
                               self.show_history,
                               "История выполненных запросов"))
        toolbar.addWidget(_btn("🗑 Очистить", "#5A2D2D", "#7A3D3D",
                               self.clear_editor,
                               "Очистить редактор"))
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Введите SQL запрос...\n\n"
            "F5 или Ctrl+Enter — выполнить\n"
            "Ctrl+Space — автодополнение")
        self.editor.setFont(_monospace_font(11))
        self.editor.setStyleSheet(
            "QTextEdit{background:#1E1E1E;color:#D4D4D4;"
            "border:1px solid #303030;border-radius:4px;padding:10px;}"
            "QTextEdit:focus{border:1px solid #569CD6;}")

        self.highlighter = SQLHighlighter(self.editor.document())
        self.auto_complete = SQLAutoComplete(self.editor)
        self.editor.installEventFilter(self)

        layout.addWidget(self.editor)
        self.explain_dialog = ExplainQueryDialog(self)

    # ----- public API -----

    def set_connection(self, connection):
        self.db_connection = connection
        if connection:
            self.auto_complete.load_schema(connection)

    def set_async_manager(self, async_manager):
        self.async_manager = async_manager

    def execute_query(self):
        query = self.editor.toPlainText().strip()
        if not query:
            return
        if not self.db_connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте БД!")
            return
        self.query_executed.emit(query, True, 0)

    def explain_query(self):
        query = self.editor.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите запрос!")
            return
        if not self.db_connection:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте БД!")
            return
        try:
            cur = self.db_connection.cursor()
            cur.execute(f"EXPLAIN QUERY PLAN {query}")
            rows = cur.fetchall()
            lines = ["План выполнения запроса:", "=" * 50, ""]
            for row in rows:
                detail = row[3] if len(row) >= 4 and row[3] else str(row)
                lines.append(f"  → {detail}")
            if not rows:
                lines.append("  (Нет данных)")
            lines += ["", "=" * 50, "", "Советы:",
                      "- Используйте INDEX для больших таблиц",
                      "- Избегайте SELECT *",
                      "- Применяйте WHERE для фильтрации"]
            self.explain_dialog.set_plan("\n".join(lines))
            self.explain_dialog.show()
            db_logger.info("EXPLAIN выполнен")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"EXPLAIN: {e}")
            db_logger.error(f"EXPLAIN: {e}")

    def show_auto_complete(self):
        self.auto_complete.show_completions()

    def show_history(self):
        if not self.history_dialog:
            self.history_dialog = QueryHistoryDialog(self.history, self)
            self.history_dialog.query_selected.connect(self._load_query)
        self.history_dialog.refresh_list()
        self.history_dialog.show()
        self.history_dialog.raise_()

    def _load_query(self, q: str):
        self.editor.setText(q)

    def clear_editor(self):
        self.editor.clear()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_F5:
                self.execute_query()
                return True
            if (event.modifiers() == Qt.KeyboardModifier.ControlModifier
                    and event.key() == Qt.Key.Key_Return):
                self.execute_query()
                return True
            if (event.modifiers() == Qt.KeyboardModifier.ControlModifier
                    and event.key() == Qt.Key.Key_Space):
                self.show_auto_complete()
                return True
        return super().eventFilter(obj, event)


# ---------------- History dialog ----------------

class QueryHistoryDialog(QDialog):

    query_selected = pyqtSignal(str)

    DIALOG_STYLE = """
        QDialog { background-color: #1e1e1e; }
        QLabel { color: #c0c0c0; font-size: 13px; }
        QLineEdit {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #303030;
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 13px;
        }
        QLineEdit:focus { border-color: #569CD6; }
        QListWidget {
            background-color: #151515;
            color: #e0e0e0;
            border: 1px solid #303030;
            border-radius: 4px;
            font-size: 12px;
            outline: none;
        }
        QListWidget::item {
            padding: 8px 10px;
            border-bottom: 1px solid #252525;
        }
        QListWidget::item:selected {
            background-color: #2a4060;
            color: #ffffff;
        }
        QListWidget::item:hover {
            background-color: #252525;
        }
        QPushButton {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #303030;
            border-radius: 4px;
            padding: 6px 16px;
            font-size: 12px;
        }
        QPushButton:hover { background-color: #3d3d3d; }
        QPushButton:pressed { background-color: #252525; }
    """

    def __init__(self, history: QueryHistory, parent=None):
        super().__init__(parent)
        self.history = history
        self.setWindowTitle("История запросов")
        self.setMinimumSize(720, 480)
        self.resize(820, 560)
        self.setStyleSheet(self.DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- поиск ---
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Поиск:")
        search_label.setStyleSheet("color:#a0a0a0; font-size:13px;")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для фильтрации...")
        self.search_input.textChanged.connect(self.filter_history)
        search_layout.addWidget(self.search_input, 1)
        layout.addLayout(search_layout)

        # --- список ---
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_select)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget, 1)

        # --- кнопки ---
        btns = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.refresh_list)
        btns.addWidget(refresh_btn)

        clear_btn = QPushButton("🗑 Очистить историю")
        clear_btn.setStyleSheet(
            "QPushButton{background:#5a2d2d;color:white;border:none;"
            "border-radius:4px;padding:6px 16px;font-size:12px;}"
            "QPushButton:hover{background:#7a3d3d;}")
        clear_btn.clicked.connect(self.clear_history)
        btns.addWidget(clear_btn)

        btns.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn)

        layout.addLayout(btns)

        # --- статистика ---
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color:#606060; font-size:11px;")
        layout.addWidget(self.stats_label)

        self.refresh_list()

    # -------- логика --------

    def refresh_list(self):
        self.list_widget.clear()
        self._fill(self.history.get_all())
        self._update_stats()

    def filter_history(self, pattern: str):
        self.list_widget.clear()
        if not pattern.strip():
            self.refresh_list()
            return
        self._fill(self.history.search(pattern))
        self.stats_label.setText(
            f"Найдено: {self.list_widget.count()} из {len(self.history.get_all())}")

    def _fill(self, entries):
        for entry in entries:
            q = entry["query"].strip().replace("\n", " ")
            preview = q[:150] + "..." if len(q) > 150 else q
            ts = entry["timestamp"][:19].replace("T", " ")
            status = "✓" if entry["success"] else "✗"
            count = entry["result_count"]
            item = QListWidgetItem(
                f"  {status}  {ts}   |   {count} строк   |   {preview}")
            item.setData(Qt.ItemDataRole.UserRole, entry["query"])
            item.setForeground(
                QColor("#90EE90") if entry["success"] else QColor("#FF6B6B"))
            item.setToolTip(entry["query"])
            self.list_widget.addItem(item)

    def _update_stats(self):
        total = len(self.history.get_all())
        ok = sum(1 for e in self.history.get_all() if e["success"])
        self.stats_label.setText(
            f"Всего записей: {total}   ·   Успешных: {ok}   ·   "
            f"С ошибкой: {total - ok}")

    def _on_select(self, item: QListWidgetItem):
        self.query_selected.emit(item.data(Qt.ItemDataRole.UserRole))
        self.accept()

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#1e1e1e;color:#e0e0e0;"
            "border:1px solid #303030;padding:4px;}"
            "QMenu::item{padding:6px 20px;border-radius:3px;}"
            "QMenu::item:selected{background:#303030;}")
        load_act = menu.addAction("📥 Загрузить в редактор")
        copy_act = menu.addAction("📋 Копировать запрос")
        menu.addSeparator()
        del_act = menu.addAction("❌ Удалить из истории")

        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == load_act:
            self._on_select(item)
        elif action == copy_act:
            QApplication.clipboard().setText(
                item.data(Qt.ItemDataRole.UserRole))
        elif action == del_act:
            q = item.data(Qt.ItemDataRole.UserRole)
            self.history.history = [e for e in self.history.get_all()
                                    if e["query"] != q]
            self.history._save()
            self.refresh_list()

    def clear_history(self):
        if QMessageBox.question(
                self, "Подтверждение",
                "Очистить всю историю запросов?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.refresh_list()