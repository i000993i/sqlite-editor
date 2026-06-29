from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from functions.logger import models_logger
from functions.utils import validate_table_name

CHART_TYPES = [
    'Столбчатая', 'Линейная', 'Круговая', 'Точечная', 'Гистограмма'
]

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib
    matplotlib.use('QtAgg')
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False


class DataVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = None
        self._data_cache = {}
        self._updating = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        controls_layout.addWidget(QLabel("Таблица:"))
        self.table_combo = QComboBox()
        self.table_combo.setMinimumWidth(160)
        self.table_combo.currentTextChanged.connect(self._on_table_changed)
        controls_layout.addWidget(self.table_combo, 1)

        controls_layout.addWidget(QLabel("X:"))
        self.x_combo = QComboBox()
        self.x_combo.setMinimumWidth(120)
        controls_layout.addWidget(self.x_combo, 1)

        controls_layout.addWidget(QLabel("Y:"))
        self.y_combo = QComboBox()
        self.y_combo.setMinimumWidth(120)
        controls_layout.addWidget(self.y_combo, 1)

        controls_layout.addWidget(QLabel("Тип:"))
        self.chart_combo = QComboBox()
        for t in CHART_TYPES:
            self.chart_combo.addItem(t)
        controls_layout.addWidget(self.chart_combo)

        self.build_btn = QPushButton("Построить")
        self.build_btn.clicked.connect(self.build_chart)
        controls_layout.addWidget(self.build_btn)

        layout.addWidget(controls)

        if not MATPLOTLIB_OK:
            layout.addWidget(QLabel("matplotlib не установлен. Установите: pip install matplotlib"))
            self.canvas = None
            self.setLayout(layout)
            return

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.figure.patch.set_facecolor('#1e1e1e')
        self.canvas = FigureCanvas(self.figure)

        from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setStyleSheet("""
            QToolBar { background: #2d2d2d; border: none; spacing: 4px; padding: 2px; }
            QToolButton { color: #e0e0e0; background: #3d3d3d; border: none;
                border-radius: 3px; padding: 3px 8px; }
            QToolButton:hover { background: #555; }
        """)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def set_db_manager(self, db_manager):
        self.db_manager = db_manager
        self._refresh_tables()

    def _refresh_tables(self):
        self._updating = True
        self.table_combo.blockSignals(True)
        self.table_combo.clear()
        self.table_combo.blockSignals(False)
        self._updating = False
        if not self.db_manager:
            return
        tables = self.db_manager.get_tables()
        valid = []
        for t in tables:
            name = t.get('name', '') if isinstance(t, dict) else str(t)
            if validate_table_name(name):
                valid.append(name)
        self._updating = True
        self.table_combo.blockSignals(True)
        self.table_combo.addItems(valid)
        self.table_combo.blockSignals(False)
        self._updating = False
        self._data_cache.clear()

    def _on_table_changed(self, table_name):
        if self._updating:
            return
        self.x_combo.clear()
        self.y_combo.clear()
        if not table_name or not self.db_manager or not validate_table_name(table_name):
            return
        schema = self.db_manager.get_table_schema(table_name)
        if not schema:
            return
        cols = [c['name'] for c in schema['columns']]
        self.x_combo.addItems(cols)
        self.y_combo.addItems(cols)
        if len(cols) > 1:
            self.y_combo.setCurrentIndex(1)

    def set_current_table(self, table_name):
        if not table_name or not validate_table_name(table_name):
            return
        idx = self.table_combo.findText(table_name)
        if idx >= 0:
            self.table_combo.setCurrentIndex(idx)

    def auto_build(self, table_name):
        if not table_name or not self.db_manager:
            return
        self._updating = True
        self.table_combo.blockSignals(True)
        self.set_current_table(table_name)
        self.table_combo.blockSignals(False)
        self._updating = False
        self._on_table_changed(table_name)
        schema = self.db_manager.get_table_schema(table_name)
        if not schema:
            return
        cols = [c['name'] for c in schema['columns']]
        if len(cols) >= 1:
            self.x_combo.setCurrentIndex(0)
        if len(cols) >= 2:
            self.y_combo.setCurrentIndex(1)
        QTimer.singleShot(0, self.build_chart)

    def refresh_tables(self):
        self._data_cache.clear()
        self._refresh_tables()

    def _load_data(self, table_name):
        if not self.db_manager or not validate_table_name(table_name):
            return None
        if table_name in self._data_cache:
            return self._data_cache[table_name]
        try:
            safe = f'"{table_name}"'
            import pandas as pd
            conn = self.db_manager.connection
            if conn is None:
                return None
            df = pd.read_sql_query(f"SELECT * FROM {safe} LIMIT 10000", conn)
            self._data_cache[table_name] = df
            return df
        except Exception as e:
            models_logger.error(f"Ошибка загрузки данных для графика: {e}")
            return None

    def build_chart(self):
        if not MATPLOTLIB_OK:
            QMessageBox.warning(self, "Ошибка", "matplotlib не установлен")
            return
        table = self.table_combo.currentText()
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        chart_type = self.chart_combo.currentText()

        if not table or not x_col:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу и колонку X")
            return

        df = self._load_data(table)
        if df is None or df.empty:
            QMessageBox.warning(self, "Ошибка", "Нет данных для построения графика")
            return

        if x_col not in df.columns:
            QMessageBox.warning(self, "Ошибка", f"Колонка '{x_col}' не найдена")
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#2d2d2d')
        ax.tick_params(colors='#e0e0e0')
        ax.spines['bottom'].set_color('#555')
        ax.spines['left'].set_color('#555')
        ax.spines['top'].set_color('#555')
        ax.spines['right'].set_color('#555')
        ax.xaxis.label.set_color('#e0e0e0')
        ax.yaxis.label.set_color('#e0e0e0')
        ax.title.set_color('#e0e0e0')

        try:
            if chart_type == 'Столбчатая':
                if y_col and y_col in df.columns:
                    data = df.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(50)
                else:
                    data = df[x_col].value_counts().head(50)
                data.plot(kind='bar', ax=ax, color='#ff4444', edgecolor='none')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col if y_col and y_col in df.columns else 'Количество')
                self.figure.autofmt_xdate()

            elif chart_type == 'Линейная':
                if y_col and y_col in df.columns:
                    data = df.groupby(x_col)[y_col].sum().sort_index()
                else:
                    data = df[x_col].value_counts().sort_index()
                data.plot(kind='line', ax=ax, color='#ff4444', linewidth=2)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col if y_col and y_col in df.columns else 'Количество')
                self.figure.autofmt_xdate()

            elif chart_type == 'Круговая':
                if y_col and y_col in df.columns:
                    data = df.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(20)
                else:
                    data = df[x_col].value_counts().head(20)
                if data.empty:
                    QMessageBox.warning(self, "Ошибка", "Недостаточно данных для круговой диаграммы")
                    return
                colors_list = ['#ff4444', '#ff6644', '#ff8844', '#ffaa44',
                               '#44ff44', '#44aaff', '#4444ff', '#aa44ff']
                data.plot(kind='pie', ax=ax, labels=data.index, colors=colors_list,
                         autopct='%1.1f%%', startangle=90)
                ax.set_ylabel('')
                ax.set_xlabel(x_col)

            elif chart_type == 'Точечная':
                if not y_col or y_col not in df.columns:
                    QMessageBox.warning(self, "Ошибка", "Для точечного графика нужны колонки X и Y")
                    return
                if df[x_col].dtype not in ('int64', 'float64') or df[y_col].dtype not in ('int64', 'float64'):
                    QMessageBox.warning(self, "Ошибка", "Точечный график требует числовые колонки")
                    return
                sample = df.sample(min(5000, len(df))) if len(df) > 5000 else df
                ax.scatter(sample[x_col], sample[y_col], alpha=0.5, s=10, color='#ff4444')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)

            elif chart_type == 'Гистограмма':
                col = x_col
                if col not in df.columns or df[col].dtype not in ('int64', 'float64'):
                    QMessageBox.warning(self, "Ошибка", "Гистограмма требует числовую колонку")
                    return
                ax.hist(df[col].dropna(), bins=50, color='#ff4444', alpha=0.8, edgecolor='none')
                ax.set_xlabel(col)
                ax.set_ylabel('Частота')

            ax.set_title(f"{chart_type}: {table}", color='#e0e0e0', fontsize=12)
            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            models_logger.error(f"Ошибка построения графика: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось построить график:\n{e}")
