from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class HistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("История запросов")
        self.setGeometry(200, 200, 600, 400)
        
        # Стили для диалога
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #151515, stop:1 #1a1a1a);
            }
            QListWidget {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #303030;
                border-radius: 4px;
                font-family: monospace;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #252525;
            }
            QListWidget::item:selected {
                background-color: #303030;
                color: #ffffff;
            }
            QLabel {
                color: #a0a0a0;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #252525, stop:1 #1f1f1f);
                color: #e0e0e0;
                border: 1px solid #303030;
                border-radius: 3px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #303030;
                border-color: #404040;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Последние запросы")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Список истории
        self.list_widget = QListWidget()
        
        for item in self.history[-50:]:  # Показываем последние 50 запросов
            query = item['query']
            if len(query) > 100:
                query = query[:97] + "..."
            self.list_widget.addItem(f"[{item['time']}] {query}")
        
        layout.addWidget(self.list_widget)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        copy_btn = QPushButton("Копировать")
        copy_btn.clicked.connect(self.copy_selected)
        btn_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def copy_selected(self):
        current = self.list_widget.currentItem()
        if current:
            text = current.text()
            # Убираем временную метку
            if '] ' in text:
                text = text.split('] ', 1)[1]
            QApplication.clipboard().setText(text)