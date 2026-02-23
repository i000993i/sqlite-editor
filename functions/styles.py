from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtGui import QLinearGradient, QPalette, QBrush, QColor

class Styles:
    # Градиентные стили для главного окна
    MAIN_WINDOW = """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0a0a0a, stop:0.5 #1a1a1a, stop:1 #0f0f0f);
        }
    """
    
    MENU_BAR = """
        QMenuBar {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0a0a0a, stop:1 #1a1a1a);
            color: #e0e0e0;
            border-bottom: 1px solid #303030;
            padding: 2px;
        }
        QMenuBar::item {
            background: transparent;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QMenuBar::item:selected {
            background: #303030;
            color: #ffffff;
        }
        QMenuBar::item:pressed {
            background: #404040;
        }
        QMenu {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a1a, stop:1 #0f0f0f);
            color: #e0e0e0;
            border: 1px solid #303030;
            padding: 2px;
        }
        QMenu::item {
            padding: 5px 20px;
            border-radius: 2px;
        }
        QMenu::item:selected {
            background: #303030;
            color: #ffffff;
        }
        QMenu::separator {
            height: 1px;
            background: #303030;
            margin: 5px 0;
        }
    """
    
    TOOLBAR = """
        QToolBar {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0f0f0f, stop:1 #1a1a1a);
            border: none;
            border-bottom: 1px solid #303030;
            spacing: 3px;
            padding: 3px;
        }
        QToolButton {
            background: transparent;
            color: #e0e0e0;
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 5px 8px;
            font-weight: normal;
        }
        QToolButton:hover {
            background: #303030;
            border: 1px solid #404040;
        }
        QToolButton:pressed {
            background: #404040;
        }
    """
    
    STATUS_BAR = """
        QStatusBar {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0a0a0a, stop:1 #1a1a1a);
            color: #808080;
            border-top: 1px solid #303030;
            padding: 3px;
        }
    """
    
    LEFT_PANEL = """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #121212, stop:1 #1a1a1a);
            border-right: 1px solid #303030;
        }
    """
    
    RIGHT_PANEL = """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0f0f0f, stop:1 #151515);
        }
    """
    
    PANEL_TITLE = """
        QLabel {
            color: #a0a0a0;
            font-size: 11px;
            font-weight: bold;
            padding: 5px 0;
            letter-spacing: 1px;
        }
    """
    
    INFO_FRAME = """
        QFrame {
            background: #1a1a1a;
            border: 1px solid #303030;
            border-radius: 4px;
            margin: 5px 0 15px 0;
        }
    """
    
    TREE_WIDGET = """
        QTreeWidget {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #303030;
            border-radius: 4px;
            outline: none;
            show-decoration-selected: 1;
        }
        QTreeWidget::item {
            padding: 5px;
            border-bottom: 1px solid #252525;
        }
        QTreeWidget::item:selected {
            background-color: #303030;
            color: #ffffff;
        }
        QTreeWidget::item:hover {
            background-color: #252525;
        }
        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {
            border-image: none;
            image: url(none);
        }
        QHeaderView::section {
            background-color: #202020;
            color: #a0a0a0;
            padding: 5px;
            border: none;
            border-bottom: 1px solid #303030;
            font-weight: bold;
        }
    """
    
    TAB_WIDGET = """
        QTabWidget::pane {
            border: 1px solid #303030;
            border-radius: 4px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #151515, stop:1 #1a1a1a);
            top: -1px;
        }
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #202020, stop:1 #1a1a1a);
            color: #808080;
            padding: 8px 15px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border: 1px solid #303030;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #303030, stop:1 #252525);
            color: #ffffff;
            border-color: #404040;
        }
        QTabBar::tab:hover:!selected {
            background: #252525;
            color: #e0e0e0;
        }
    """
    
    SQL_BUTTON = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #252525, stop:1 #1f1f1f);
            color: #e0e0e0;
            border: 1px solid #303030;
            border-radius: 3px;
            padding: 5px 15px;
            font-weight: normal;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #303030, stop:1 #252525);
            border-color: #404040;
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1a1a1a, stop:1 #1f1f1f);
        }
    """
    
    SQL_EDITOR = """
        QTextEdit {
            background-color: #1a1a1a;
            color: #e0e0e0;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            border: 1px solid #303030;
            border-radius: 4px;
            padding: 10px;
            selection-background-color: #404040;
        }
        QTextEdit:focus {
            border-color: #505050;
        }
    """
    
    SPLITTER = """
        QSplitter::handle {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #202020, stop:1 #303030);
            width: 1px;
        }
        QSplitter::handle:hover {
            background: #404040;
        }
    """

class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Ключевые слова SQL
        keywords = [
            "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER",
            "TABLE", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL",
            "ON", "AND", "OR", "NOT", "NULL", "IS", "LIKE", "IN", "BETWEEN",
            "VALUES", "SET", "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET",
            "PRIMARY", "FOREIGN", "KEY", "REFERENCES", "CONSTRAINT", "UNIQUE",
            "INDEX", "VIEW", "TRIGGER", "FUNCTION", "PROCEDURE", "BEGIN", "COMMIT",
            "ROLLBACK", "TRANSACTION", "SAVEPOINT", "RELEASE", "CASCADE", "RESTRICT"
        ]
        
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(160, 160, 160))  # Серый для ключевых слов
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        for word in keywords:
            pattern = f"\\b{word}\\b"
            rule = (QRegularExpression(pattern, QRegularExpression.PatternOption.CaseInsensitiveOption), 
                   keyword_format)
            self.highlighting_rules.append(rule)
        
        # Строки
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(180, 180, 180))  # Светло-серый для строк
        rule = (QRegularExpression("'.*'"), string_format)
        self.highlighting_rules.append(rule)
        rule = (QRegularExpression("\".*\""), string_format)
        self.highlighting_rules.append(rule)
        
        # Числа
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(200, 200, 200))  # Очень светлый серый для чисел
        rule = (QRegularExpression("\\b\\d+\\b"), number_format)
        self.highlighting_rules.append(rule)
        
        # Комментарии
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(80, 80, 80))  # Темно-серый для комментариев
        comment_format.setFontItalic(True)
        rule = (QRegularExpression("--[^\n]*"), comment_format)
        self.highlighting_rules.append(rule)
        rule = (QRegularExpression("/\\*.*\\*/"), comment_format)
        self.highlighting_rules.append(rule)
        
        # Функции
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(140, 140, 140))  # Серый для функций
        rule = (QRegularExpression("\\b[A-Za-z_]+\\(.*\\)"), function_format)
        self.highlighting_rules.append(rule)
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)