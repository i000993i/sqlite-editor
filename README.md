================================================================================
                        SQLITE TABLE VIEWER
================================================================================

Кроссплатформенный просмотрщик и редактор SQLite баз данных с тёмной темой.

Версия 2.1 | Python 3.10+ | PyQt6 | pandas | NumPy | matplotlib | MIT License
CI/CD: GitHub Actions (Windows x64, Linux .deb / AppImage)

--------------------------------------------------------------------------------
1. О ПРИЛОЖЕНИИ
--------------------------------------------------------------------------------

SQLite Table Viewer — это десктопное приложение для просмотра, редактирования
и анализа баз данных SQLite. Написано на Python с использованием PyQt6 и
оформлено в единой тёмной теме.

Приложение работает под Windows 10/11 (x64) и Linux (Ubuntu, Debian,
Zorin OS и другие дистрибутивы на базе GNOME). Все сборки автоматизированы
через GitHub Actions — релизы содержат .exe, .deb и .AppImage.

При запуске показывается заставка (splash screen) с прогрессом
инициализации. Благодаря постраничной загрузке (виртуальная прокрутка)
приложение открывает таблицы с миллионами записей, не загружая данные
в память целиком. Все операции записи защищены блокировкой RLock, а
длительные запросы выполняются в фоновых потоках с возможностью отмены.

ВОЗМОЖНОСТИ:
  * Работа с БД: открытие .db, .sqlite, .db3, создание новых баз.
  * Виртуальная прокрутка: постраничная загрузка (50–1000 строк,
    по умолчанию 100).
  * Редактирование: ячейки, добавление/удаление строк и колонок.
  * Поиск по всем колонкам таблицы.
  * SQL-редактор: подсветка синтаксиса, автодополнение, история запросов,
    EXPLAIN QUERY PLAN.
  * Графики: столбчатые, линейные, круговые, точечные, гистограммы,
    матрица корреляции.
  * Аналитика на pandas/NumPy: описательная статистика, пропуски, выбросы,
    группировки, корреляции.
  * Импорт CSV и JSON.
  * Экспорт в CSV, JSON, Excel (до 1M строк), PDF (до 10K строк).
  * Инструменты: резервное копирование, оптимизация VACUUM.
  * Тёмная тема с единым стилем для всех ОС.
  * Потокобезопасность: RLock для SQLite, interrupt() для отмены запросов.

--------------------------------------------------------------------------------
2. ПОЛНАЯ СТРУКТУРА ПАПОК
--------------------------------------------------------------------------------

sqlite-table-viewer/
|
+-- main.py                          # Точка входа приложения (UI + заставка)
+-- build.py                         # Единый скрипт сборки (Windows/Linux)
+-- build_app.ps1                    # Обёртка PowerShell для Windows
+-- build_app.sh                     # Обёртка bash для Linux
+-- requirements.txt                 # Зависимости
+-- README.md                        # Этот файл
+-- LICENSE                          # MIT
+-- SQLiteViewer.spec                # PyInstaller spec-файл (GUI-сборка)
+-- SQLiteViewer_console.spec        # PyInstaller spec (консольная отладка)
|
+-- .github/
|   +-- workflows/
|       +-- build.yml                # CI: Windows x64, Linux AppImage + .deb
|
+-- .gitignore
|
+-- packaging/
|   +-- linux/
|       +-- sqlite-viewer.desktop    # Ярлык для Linux
|       +-- build_deb.sh             # Локальная сборка .deb (опционально)
|
+-- docs/
|   +-- SQL_EDITOR_GUIDE.md          # Руководство по SQL-редактору
|
+-- functions/                       # Ядро приложения
|   +-- __init__.py                  # Ленивый пакет (без побочных импортов)
|   +-- paths.py                     # Кроссплатформенные пути
|   +-- logger.py                    # Настройка логирования
|   +-- utils.py                     # Валидация, хелперы, format_size
|   +-- styles.py                    # CSS-стили и SQLHighlighter
|   +-- database.py                  # DatabaseManager (RLock + интерфейс к SQLite)
|   +-- async_manager.py             # QThread + SchemaCache + interrupt()
|   +-- virtual_table_model.py       # QAbstractTableModel с постраничной загрузкой
|   +-- table_viewer_virtual.py      # Виджет таблицы (пагинация, поиск, правка)
|   +-- sql_editor.py                # SQL-редактор + история + EXPLAIN
|   +-- table_designer.py            # Визуальный редактор схемы
|   +-- data_visualizer.py           # matplotlib-графики
|   +-- data_analysis.py             # класс DataAnalysis (pandas/NumPy)
|   +-- import_export.py             # Импорт/экспорт CSV, JSON, Excel, PDF
|
+-- icons/
|   +-- app.png                      # Иконка приложения для Linux
|   +-- app_icon.ico                 # Иконка приложения для Windows
|   +-- splash.png                   # Ресурс заставки
|   +-- gradient_bg.png              # Фоновый градиент
|   +-- database.svg                 # UI-иконки
|   +-- table.svg
|   +-- sql.svg
|   +-- open.svg
|   +-- new.svg
|   +-- refresh.svg
|   +-- import.svg
|   +-- export.svg
|   +-- search.svg
|   +-- limit.svg
|
+-- logs/                            # Только для локальной разработки
|   +-- (в релизах пишутся в user_data)
|
+-- tests/
    +-- test_database.py             # Потокобезопасность, CRUD
    +-- test_data_analysis.py        # null_report, correlation, outliers
    +-- test_utils.py                # Валидация имён, format_size

Примечание: каталоги logs/ и dist/ создаются при запуске/сборке,
в репозиторий не входят.

--------------------------------------------------------------------------------
3. УСТАНОВКА
--------------------------------------------------------------------------------

ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ:
  * Python 3.10+
  * pip
  * Системные библиотеки:
      Linux:   libgl1 libegl1 libxkbcommon0 libxcb-cursor0 libfuse2
               fonts-dejavu-core
      Windows: ничего дополнительно

ИЗ ИСХОДНИКОВ:
  git clone https://github.com/yourusername/sqlite-table-viewer.git
  cd sqlite-table-viewer

  python -m venv .venv
  source .venv/bin/activate          # Linux
  # .venv\Scripts\activate           # Windows

  pip install -r requirements.txt
  python main.py

ИЗ ГОТОВОГО РЕЛИЗА (скачать со страницы Releases):

  Windows 10/11 (x64)    : SQLiteViewer.exe в папке sqlite-viewer-windows-x64
  Linux (Ubuntu/Zorin)   : sqlite-viewer_<version>_amd64.deb
  Универсальный Linux    : SQLiteViewer-x86_64.AppImage

Установка .deb:
  sudo dpkg -i sqlite-viewer_*.deb
  sudo apt-get install -f        # если не хватает зависимостей

Запуск AppImage:
  chmod +x SQLiteViewer-x86_64.AppImage
  ./SQLiteViewer-x86_64.AppImage

ВАЖНО ДЛЯ LINUX / ZORIN OS:
  При ошибке "GLib-GIO-ERROR ... antialiasing" (несовместимость Qt/Wayland
  с GNOME) запустите:
      GDK_BACKEND=x11 ./SQLiteViewer-x86_64.AppImage
  Для .deb-версии:
      GDK_BACKEND=x11 sqlite-viewer

--------------------------------------------------------------------------------
4. ЗАВИСИМОСТИ
--------------------------------------------------------------------------------

  PyQt6>=6.4.0
  pandas>=2.0.0
  numpy>=1.24.0
  openpyxl>=3.0.0
  reportlab>=4.0.0
  matplotlib>=3.7.0

  # Тесты
  pytest>=7.0.0
  pytest-qt>=4.2.0
  pytest-cov>=4.0.0
  pytest-xdist>=3.0.0

  # Сборка
  pyinstaller>=6.0.0

--------------------------------------------------------------------------------
5. ИСПОЛЬЗОВАНИЕ
--------------------------------------------------------------------------------

  1. Файл -> Открыть базу данных (Ctrl+O)
  2. Двойной клик по таблице в левой панели
  3. Просмотр данных с поиском и постраничной навигацией
  4. Вкладка "SQL запросы" — редактор, подсветка, автодополнение
  5. Вкладка "Конструктор таблиц" — визуальное редактирование схемы
  6. Вкладка "Графики" — визуализация и отчёт

ГОРЯЧИЕ КЛАВИШИ:
  Ctrl+O          Открыть базу данных
  Ctrl+N          Создать новую БД
  Ctrl+Q          Выход
  F5 / Ctrl+Enter Выполнить SQL-запрос (в редакторе SQL)
  Ctrl+Space      Автодополнение SQL

Поиск по таблице выполняется через поле "Поиск по таблице..."
(поиск по всем колонкам, дебаунс 300 мс).

ЦВЕТОВАЯ СХЕМА:
  Тёмная тема в нейтральных серых тонах:
  Фон             : #0a0a0a, #0f0f0f, #1a1a1a
  Панели/рамки    : #303030, #404040
  Текст           : #e0e0e0, #ffffff
  Акцент (успех)  : зелёный #2a4a2a / #90EE90

--------------------------------------------------------------------------------
6. РАБОТА С БОЛЬШИМИ ДАННЫМИ
--------------------------------------------------------------------------------

  * Постраничная загрузка (50–1000 строк, по умолчанию 100).
  * Автоподгрузка при прокрутке к концу страницы.
  * SQL-запросы в фоновом потоке с отменой (connection.interrupt()).
  * Импорт/экспорт чанками по 10 000 записей.
  * Кэширование схемы и страниц (до 20 страниц).
  * Ограничения: Excel — 1 000 000 строк, PDF — 10 000 строк.

--------------------------------------------------------------------------------
7. ИМПОРТ И ЭКСПОРТ
--------------------------------------------------------------------------------

  Формат   Импорт   Экспорт
  ------   ------   -------
  CSV      да       да (UTF-8 BOM)
  JSON     да       да
  Excel    —        да (до 1M строк)
  PDF      —        да (до 10K строк)

--------------------------------------------------------------------------------
8. АНАЛИТИКА ДАННЫХ
--------------------------------------------------------------------------------

Модуль functions/data_analysis.py содержит класс DataAnalysis (pandas/NumPy),
все методы статические:

  * DataAnalysis.from_query(connection, query, limit=100_000) — DataFrame из запроса
  * DataAnalysis.from_table(connection, table, limit=100_000) — DataFrame из таблицы
  * DataAnalysis.describe(df)            — описательная статистика (транспонированная)
  * DataAnalysis.null_report(df)         — отчёт по пропускам (null_count, null_pct, dtype)
  * DataAnalysis.detect_column_types(df) — определение типов колонок
  * DataAnalysis.correlation(df, method="pearson") — матрица корреляций
  * DataAnalysis.outliers_iqr(df, column)          — выбросы методом IQR
  * DataAnalysis.group_aggregate(df, group_col, value_col, agg, top=50) — группировки
  * DataAnalysis.full_report(df)         — сводный отчёт (строки, типы, пропуски, корреляции)

Все эти функции доступны через кнопку "Отчёт" во вкладке "Графики",
а матрица корреляций строится как отдельный тип графика.

--------------------------------------------------------------------------------
9. ЛОГИРОВАНИЕ
--------------------------------------------------------------------------------

Логи пишутся в пользовательский каталог:
  Windows : %APPDATA%\SQLiteViewer\logs\
  Linux   : ~/.local/share/SQLiteViewer/logs/

Файлы: app.log, database.log, models.log, utils.log.
История SQL-запросов: <user_data>/query_history.json.

--------------------------------------------------------------------------------
10. СБОРКА
--------------------------------------------------------------------------------

ЛОКАЛЬНАЯ СБОРКА:

  Windows 10/11:
      .\build_app.ps1
      .\build_app.ps1 -Console      # консольная версия (отладка)
      # или
      python build.py [--console]

  Linux (Zorin / Ubuntu / Debian):
      chmod +x build_app.sh
      ./build_app.sh
      ./build_app.sh --console      # консольная версия (отладка)
      # или
      python3 build.py [--console]

Результат: dist/SQLiteViewer/SQLiteViewer[.exe].

ЧТО ДЕЛАЕТ build.py:
  1. Генерирует заглушки иконок, если app.png/app.ico отсутствуют.
  2. Устанавливает зависимости из requirements.txt и PyInstaller.
  3. Очищает build/ и dist/.
  4. Запускает PyInstaller с SQLiteViewer.spec (с флагом --console
     для отладочной сборки с консолью).
  5. Копирует папку icons/ в сборку.
  6. Печатает путь к готовому бинарнику.

GITHUB ACTIONS:
Файл .github/workflows/build.yml содержит три job'а:

  Job              Матрица             Артефакты
  ---------------  ------------------  ------------------------------
  build-linux      appimage, deb       .AppImage, .deb
  build-windows    x64                 папка dist/SQLiteViewer/
  release          —                   публикация в GitHub Releases при теге v*

ТРИГГЕРЫ:
  * Push в main / master -> артефакты доступны на вкладке Actions.
  * Pull Request -> артефакты (без публикации релиза).
  * Тег v* -> автоматическая публикация в Releases.
  * Ручной запуск: Actions -> Build & Release -> Run workflow.

ПУБЛИКАЦИЯ РЕЛИЗА:
  git tag v1.0.0
  git push origin v1.0.0

После успешной сборки в Releases появятся:
  SQLiteViewer-x86_64.AppImage
  sqlite-viewer_1.0.0_amd64.deb
  папка sqlite-viewer-windows-x64/ (SQLiteViewer.exe + библиотеки)

СБОРКА .DEB ВРУЧНУЮ:
  sudo apt install fakeroot dpkg-dev desktop-file-utils
  bash packaging/linux/build_deb.sh

Скрипт:
  1. Копирует dist/SQLiteViewer/ в pkg/opt/sqlite-viewer/.
  2. Создаёт ярлык /usr/bin/sqlite-viewer.
  3. Кладёт .desktop и иконку.
  4. Формирует DEBIAN/control с зависимостями.
  5. Запускает dpkg-deb --build.

СБОРКА APPIMAGE ВРУЧНУЮ:
  # 1. Соберите бинарник
  python3 build.py

  # 2. Сформируйте AppDir
  APP_DIR=AppDir
  mkdir -p $APP_DIR/usr/bin $APP_DIR/usr/share/applications \
           $APP_DIR/usr/share/icons/hicolor/256x256/apps
  cp -r dist/SQLiteViewer/* $APP_DIR/usr/bin/
  cp icons/app.png $APP_DIR/usr/share/icons/hicolor/256x256/apps/sqlite-viewer.png
  cp packaging/linux/sqlite-viewer.desktop $APP_DIR/usr/share/applications/

  cat > $APP_DIR/AppRun <<'EOF'
  #!/bin/bash
  HERE="$(dirname "$(readlink -f "${0}")")"
  export LD_LIBRARY_PATH="$HERE/usr/bin:$LD_LIBRARY_PATH"
  exec "$HERE/usr/bin/SQLiteViewer" "$@"
  EOF
  chmod +x $APP_DIR/AppRun

  # 3. Соберите AppImage
  wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x appimagetool-x86_64.AppImage
  ARCH=x86_64 ./appimagetool-x86_64.AppImage --appimage-extract-and-run \
      AppDir SQLiteViewer-x86_64.AppImage

СПЕЦИФИКА СБОРКИ ПОД WINDOWS:
  * PyInstaller на Windows автоматически подхватывает DLL из PyQt6.
  * SQLiteViewer.spec использует icons/app.ico (если есть) как иконку exe.
  * Отдельный SQLiteViewer_console.spec — консольная сборка для отладки.
  * Антивирусы иногда ругаются на PyInstaller-бинарники — это известный
    false positive; можно подписать код (Code Signing), но для open-source
    проекта это не обязательно.

ПРОВЕРКА СБОРКИ:
  Windows:
    dist\SQLiteViewer\SQLiteViewer.exe
  Linux:
    ./dist/SQLiteViewer/SQLiteViewer
    ./SQLiteViewer-x86_64.AppImage
    sudo dpkg -i sqlite-viewer_*.deb && sqlite-viewer

--------------------------------------------------------------------------------
11. ТЕСТИРОВАНИЕ
--------------------------------------------------------------------------------

  pip install pytest pytest-qt pytest-cov pytest-xdist

  pytest -v
  pytest --cov=functions tests/ --cov-report=html
  pytest -n auto                    # параллельно

Тесты покрывают:
  * test_database.py              — CRUD, потокобезопасность, валидация имён
  * test_data_analysis.py         — null_report, correlation, outliers, group_aggregate
  * test_utils.py                 — валидация имён таблиц/колонок, format_size

--------------------------------------------------------------------------------
12. РАЗРАБОТКА
--------------------------------------------------------------------------------

ДОБАВЛЕНИЕ НОВОГО МОДУЛЯ:
  1. Создайте файл в functions/.
  2. Импортируйте локально — functions/__init__.py намеренно ленивый,
     чтобы ошибка в одном модуле не блокировала остальные.
  3. Добавьте тесты в tests/.

ПРОВЕРКА ИМПОРТОВ ВСЕХ МОДУЛЕЙ:
  python -c "
  import importlib, pkgutil, functions
  for m in pkgutil.iter_modules(functions.__path__):
      name = f'functions.{m.name}'
      try:
          importlib.import_module(name); print('OK  ', name)
      except Exception as e:
          print('FAIL', name, '->', type(e).__name__, e)
  "

--------------------------------------------------------------------------------
13. УСТРАНЕНИЕ НЕПОЛАДОК
--------------------------------------------------------------------------------

LINUX:
  Ошибка: GLib-GIO-ERROR ... antialiasing
  Решение: GDK_BACKEND=x11 ./SQLiteViewer
           (несовместимость Qt/Wayland с GNOME-схемами; Zorin OS, Ubuntu 22+)

  Ошибка: error while loading shared libraries: libxcb-cursor.so.0
  Решение: sudo apt install libxcb-cursor0

  Ошибка: AppImage не запускается
  Решение: sudo apt install libfuse2

  Ошибка: PDF не отображает кириллицу
  Решение: установите fonts-dejavu-core или fonts-noto-core

  Ошибка: Тёмная тема не применяется
  Решение: запустите с QT_QPA_PLATFORMTHEME=""

WINDOWS:
  Ошибка: Антивирус блокирует exe
  Решение: PyInstaller false positive; добавьте в исключения или подпишите.

  Ошибка: api-ms-win-crt-* не найден
  Решение: установите Visual C++ Redistributable:
           https://aka.ms/vs/17/release/vc_redist.x64.exe

  Ошибка: Шрифт Consolas отсутствует
  Решение: используется системный моноширинный, ошибка не критична.

ОБЕ ПЛАТФОРМЫ:
  Симптом: "Нет подключения к БД" при SQL
  Решение: откройте базу через Файл -> Открыть

  Симптом: Пустые графики
  Решение: нажмите "Построить"; убедитесь, что выбрана таблица и колонка X

  Симптом: История запросов не сохраняется
  Решение: проверьте права на %APPDATA%\SQLiteViewer\ /
           ~/.local/share/SQLiteViewer/

--------------------------------------------------------------------------------
14. ВКЛАД В ПРОЕКТ
--------------------------------------------------------------------------------

  1. Форкните репозиторий.
  2. Создайте ветку (git checkout -b feature/amazing-feature).
  3. Зафиксируйте изменения (git commit -m 'Add amazing feature').
  4. Запушьте (git push origin feature/amazing-feature).
  5. Откройте Pull Request.

CI автоматически соберёт артефакты под все платформы.

--------------------------------------------------------------------------------
15. ПЛАНЫ
--------------------------------------------------------------------------------

  [x] Редактирование ячеек
  [x] Автодополнение SQL
  [x] Экспорт в PDF
  [x] EXPLAIN QUERY PLAN
  [x] Подсветка синтаксиса
  [x] Визуальный редактор таблиц
  [x] Постраничная загрузка данных
  [x] Добавление/удаление строк и колонок
  [x] Графики и визуализация
  [x] Аналитика (pandas / NumPy)
  [x] CI/CD (Windows x64, Linux AppImage + .deb)
  [x] Кроссплатформенные логи и история запросов
  [x] Заставка при запуске
  [ ] Множественные вкладки SQL-запросов
  [ ] Поддержка зашифрованных БД (SQLCipher)
  [ ] Плагины

--------------------------------------------------------------------------------
16. ЛИЦЕНЗИЯ
--------------------------------------------------------------------------------

MIT — подробнее в файле LICENSE.

--------------------------------------------------------------------------------
17. КОНТАКТЫ
--------------------------------------------------------------------------------

  Issues      : https://github.com/yourusername/sqlite-table-viewer/issues
  Discussions : https://github.com/yourusername/sqlite-table-viewer/discussions

================================================================================