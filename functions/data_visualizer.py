from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
import pandas as pd

from functions.logger import models_logger
from functions.utils import validate_table_name
from functions.data_analysis import DataAnalysis

CHART_TYPES = ["Столбчатая", "Линейная", "Круговая",
               "Точечная", "Гистограмма", "Корреляция"]

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
    from matplotlib.figure import Figure
    import matplotlib
    matplotlib.use("QtAgg")
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False


class DataVisualizer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = None
        self._data_cache: dict[str, pd.DataFrame] = {}
        self._updating = False
        self._setup_ui()

    # ---------------- UI ----------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        controls = QWidget()
        h = QHBoxLayout(controls)
        h.setContentsMargins(0, 0, 0, 0)

        h.addWidget(QLabel("Таблица:"))
        self.table_combo = QComboBox(); self.table_combo.setMinimumWidth(160)
        self.table_combo.currentTextChanged.connect(self._on_table_changed)
        h.addWidget(self.table_combo, 1)

        h.addWidget(QLabel("X:"))
        self.x_combo = QComboBox(); self.x_combo.setMinimumWidth(120)
        h.addWidget(self.x_combo, 1)

        h.addWidget(QLabel("Y:"))
        self.y_combo = QComboBox(); self.y_combo.setMinimumWidth(120)
        h.addWidget(self.y_combo, 1)

        h.addWidget(QLabel("Тип:"))
        self.chart_combo = QComboBox()
        self.chart_combo.addItems(CHART_TYPES)
        h.addWidget(self.chart_combo)

        self.build_btn = QPushButton("Построить")
        self.build_btn.clicked.connect(self.build_chart)
        h.addWidget(self.build_btn)

        self.stats_btn = QPushButton("📊 Отчёт")
        self.stats_btn.setToolTip("Описательная статистика, пропуски, корреляция")
        self.stats_btn.clicked.connect(self.show_stats)
        h.addWidget(self.stats_btn)

        layout.addWidget(controls)

        if not MATPLOTLIB_OK:
            layout.addWidget(QLabel("matplotlib не установлен. "
                                    "Установите: pip install matplotlib"))
            self.canvas = None
            return

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.figure.patch.set_facecolor("#1e1e1e")
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setStyleSheet(
            "QToolBar{background:#2d2d2d;border:none;spacing:4px;padding:2px;}"
            "QToolButton{color:#e0e0e0;background:#3d3d3d;border:none;"
            "border-radius:3px;padding:3px 8px;}QToolButton:hover{background:#555;}"
        )
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    # ---------------- state ----------------

    def set_db_manager(self, db_manager):
        self.db_manager = db_manager
        self._data_cache.clear()
        self._refresh_tables()

    def _refresh_tables(self):
        self._updating = True
        self.table_combo.blockSignals(True)
        self.table_combo.clear()

        if self.db_manager:
            raw = self.db_manager.get_tables()          # [(name, count), ...]
            for item in raw:
                if isinstance(item, tuple) and item:
                    name = item[0]
                elif isinstance(item, dict):
                    name = item.get("name", "")
                else:
                    name = str(item)
                if validate_table_name(name):
                    self.table_combo.addItem(name, userData=name)

        self.table_combo.blockSignals(False)
        self._updating = False

    def _on_table_changed(self, table_name: str):
        if self._updating or not table_name or not self.db_manager:
            return
        self._fill_columns(table_name)

    def _fill_columns(self, table_name: str):
        self.x_combo.clear()
        self.y_combo.clear()
        if not validate_table_name(table_name):
            return
        schema = self.db_manager.get_table_schema(table_name)
        if not schema:
            return
        cols = [c["name"] for c in schema["columns"]]
        self.x_combo.addItems(cols)
        self.y_combo.addItems(cols)
        if len(cols) > 1:
            self.y_combo.setCurrentIndex(1)

    def set_current_table(self, table_name: str):
        if not table_name or not validate_table_name(table_name):
            return
        idx = self.table_combo.findData(table_name)
        if idx < 0:
            idx = self.table_combo.findText(table_name)
        if idx >= 0:
            self.table_combo.setCurrentIndex(idx)   # триггерит _on_table_changed

    def auto_build(self, table_name: str):
        if not table_name or not self.db_manager:
            return
        self.set_current_table(table_name)
        QTimer.singleShot(0, self.build_chart)

    def refresh_tables(self):
        self._data_cache.clear()
        self._refresh_tables()

    # ---------------- data ----------------

    def _load_data(self, table_name: str) -> pd.DataFrame | None:
        if not self.db_manager or not validate_table_name(table_name):
            return None
        if table_name in self._data_cache:
            return self._data_cache[table_name]
        try:
            df = DataAnalysis.from_table(self.db_manager.connection,
                                          table_name, limit=50_000)
            self._data_cache[table_name] = df
            return df
        except Exception as e:
            models_logger.error(f"Ошибка загрузки данных для графика: {e}")
            return None

    # ---------------- charts ----------------

    def _prepare_axes(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#2d2d2d")
        for s in ax.spines.values():
            s.set_color("#555")
        ax.tick_params(colors="#e0e0e0")
        ax.xaxis.label.set_color("#e0e0e0")
        ax.yaxis.label.set_color("#e0e0e0")
        ax.title.set_color("#e0e0e0")
        return ax

    @staticmethod
    def _is_num(df, col):
        return col in df.columns and pd.api.types.is_numeric_dtype(df[col])

    def _series(self, df, x, y, agg="sum", top=50, sort_index=False) -> pd.Series:
        if self._is_num(df, y):
            s = df.groupby(x, dropna=False)[y].agg(agg)
            return s.sort_index().head(top) if sort_index \
                else s.sort_values(ascending=False).head(top)
        s = df[x].value_counts(dropna=False)
        return s.sort_index().head(top) if sort_index else s.head(top)

    def build_chart(self):
        if not MATPLOTLIB_OK:
            return
        table = self.table_combo.currentData() or self.table_combo.currentText()
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        chart = self.chart_combo.currentText()

        if not table or not x_col:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу и колонку X")
            return
        df = self._load_data(table)
        if df is None or df.empty:
            QMessageBox.warning(self, "Ошибка", "Нет данных")
            return
        if x_col not in df.columns:
            QMessageBox.warning(self, "Ошибка", f"Нет колонки {x_col}")
            return

        try:
            ax = self._prepare_axes()

            if chart == "Столбчатая":
                s = self._series(df, x_col, y_col, "sum", top=50)
                s.plot(kind="bar", ax=ax, color="#ff4444", edgecolor="none")
                ax.set_ylabel(y_col if self._is_num(df, y_col) else "Количество")
                self.figure.autofmt_xdate()

            elif chart == "Линейная":
                s = self._series(df, x_col, y_col, "sum", top=200, sort_index=True)
                s.plot(kind="line", ax=ax, color="#ff4444", linewidth=2)
                ax.set_ylabel(y_col if self._is_num(df, y_col) else "Количество")
                self.figure.autofmt_xdate()

            elif chart == "Круговая":
                s = self._series(df, x_col, y_col, "sum", top=20)
                if s.empty:
                    QMessageBox.warning(self, "Ошибка", "Недостаточно данных")
                    return
                palette = ["#ff4444", "#ff6644", "#ff8844", "#ffaa44",
                           "#ffcc44", "#44ff88", "#44aaff", "#aa44ff",
                           "#ff44aa", "#88ff44"]
                s.plot(kind="pie", ax=ax,
                       labels=[str(i)[:20] for i in s.index],
                       colors=palette[:len(s)],
                       autopct="%1.1f%%", startangle=90,
                       textprops={"color": "#e0e0e0"})
                ax.set_ylabel("")

            elif chart == "Точечная":
                if not self._is_num(df, x_col) or not self._is_num(df, y_col):
                    QMessageBox.warning(self, "Ошибка",
                                        "Точечный график: нужны числовые X и Y")
                    return
                d = df[[x_col, y_col]].dropna()
                if len(d) > 5000:
                    d = d.sample(5000, random_state=0)
                ax.scatter(d[x_col], d[y_col], s=12, alpha=0.6, color="#ff4444")
                ax.set_xlabel(x_col); ax.set_ylabel(y_col)

            elif chart == "Гистограмма":
                if not self._is_num(df, x_col):
                    QMessageBox.warning(self, "Ошибка",
                                        "Гистограмма: нужна числовая колонка")
                    return
                vals = pd.to_numeric(df[x_col], errors="coerce").dropna()
                ax.hist(vals, bins=50, color="#ff4444", alpha=0.85, edgecolor="none")
                ax.axvline(vals.mean(), color="#44aaff", linestyle="--",
                           label=f"mean={vals.mean():.2f}")
                ax.axvline(vals.median(), color="#88ff44", linestyle="--",
                           label=f"median={vals.median():.2f}")
                ax.legend(facecolor="#2d2d2d", edgecolor="#555", labelcolor="#e0e0e0")
                ax.set_xlabel(x_col); ax.set_ylabel("Частота")

            elif chart == "Корреляция":
                corr = DataAnalysis.correlation(df)
                if corr.empty:
                    QMessageBox.warning(self, "Ошибка", "Нужны ≥2 числовые колонки")
                    return
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
                ax.set_xticks(range(len(corr.columns)))
                ax.set_yticks(range(len(corr.columns)))
                ax.set_xticklabels(corr.columns, rotation=45, ha="right",
                                   color="#e0e0e0")
                ax.set_yticklabels(corr.columns, color="#e0e0e0")
                for i in range(len(corr)):
                    for j in range(len(corr)):
                        val = corr.values[i, j]
                        ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                                color="white" if abs(val) > 0.5 else "black",
                                fontsize=8)
                self.figure.colorbar(im, ax=ax)

            ax.set_title(f"{chart}: {table}", color="#e0e0e0", fontsize=12)
            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            models_logger.error(f"Ошибка графика: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось построить:\n{e}")

    # ---------------- report ----------------

    def show_stats(self):
        table = self.table_combo.currentData() or self.table_combo.currentText()
        df = self._load_data(table) if table else None
        if df is None or df.empty:
            QMessageBox.warning(self, "Ошибка", "Нет данных")
            return
        rep = DataAnalysis.full_report(df)
        lines = [f"Таблица: {table}",
                 f"Строк: {rep['rows']}, Колонок: {rep['columns']}", ""]
        lines.append("=== Типы колонок ===")
        for c, t in rep["dtypes"].items():
            lines.append(f"  {c}: {t}")
        lines.append("")
        lines.append("=== Пропуски ===")
        for r in rep["null_report"][:20]:
            lines.append(f"  {r['column']}: {r['null_count']} ({r['null_pct']}%)")
        if rep["correlation"]:
            lines.append("")
            lines.append("=== Корреляция (фрагмент) ===")
            for col, vals in list(rep["correlation"].items())[:10]:
                lines.append(f"  {col}: {vals}")
        QMessageBox.information(self, "Анализ данных", "\n".join(lines))