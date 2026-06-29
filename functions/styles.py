from PyQt6.QtGui import QColor

class Styles:
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

    LINE_EDIT = """
        QLineEdit {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #303030;
            border-radius: 3px;
            padding: 5px 10px;
            min-width: 200px;
        }
        QLineEdit:focus {
            border-color: #505050;
        }
    """

    COMBO_BOX = """
        QComboBox {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #303030;
            border-radius: 3px;
            padding: 5px 10px;
            min-width: 70px;
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
    """

    TABLE_VIEW = """
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
    """

    TOGGLE_BUTTON = """
        QPushButton {
            background-color: #1a1a1a;
            color: #808080;
            border: 1px solid #303030;
            border-radius: 3px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #252525;
            border-color: #404040;
        }
        QPushButton:checked {
            background-color: #2a4a2a;
            color: #90EE90;
            border-color: #3a6a3a;
        }
    """
