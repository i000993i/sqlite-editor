================================================================================
                        SQLITE TABLE VIEWER
================================================================================

Кроссплатформенный просмотрщик и редактор SQLite баз данных с тёмной темой.

Python 3.10+ | PyQt6 | pandas | NumPy | MIT License
CI/CD: GitHub Actions (Windows x64/x86, Linux .deb / AppImage)

--------------------------------------------------------------------------------
1. О ПРИЛОЖЕНИИ
--------------------------------------------------------------------------------

SQLite Table Viewer — это десктопное приложение для просмотра, редактирования
и анализа баз данных SQLite. Написано на Python с использованием PyQt6 и
оформлено в единой тёмной теме.

Приложение работает под Windows 10/11 (x86 и x64) и Linux (Ubuntu, Debian,
Zorin OS и другие дистрибутивы на базе GNOME). Все сборки автоматизированы
через GitHub Actions — релизы содержат .exe, .deb и .AppImage.

Благодаря постраничной загрузке (виртуальная прокрутка) приложение открывает
таблицы с миллионами записей, не загружая данные в память целиком. Все операции
записи защищены блокировкой RLock, а длительные запросы выполняются в фоновых
потоках с возможностью отмены.

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
+-- main.py                          # Точка входа приложения
+-- build.py                         # Единый скрипт сборки (Windows/Linux)
+-- build_app.ps1                    # Обёртка PowerShell для Windows
+-- build_app.sh                     # Обёртка bash для Linux
+-- requirements.txt                 # Зависимости
+-- README.txt                       # Этот файл
+-- LICENSE                          # MIT
+-- SQLiteViewer.spec                # PyInstaller spec-файл
|
+-- .github/
|   +-- workflows/
|       +-- build.yml                # CI: Windows x64/x86, Linux AppImage + .deb
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
|   +-- BUILD.md                     # Подробная инструкция сборки
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
|   +-- data_analysis.py             # pandas/NumPy-аналитика
|   +-- import_export.py             # Импорт/экспорт CSV, JSON, Excel, PDF
|
+-- icons/
|   +-- app.png                      # Иконка приложения для Linux
|   +-- app.ico                      # Иконка приложения для Windows
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
    +-- __init__.py
    +-- test_database.py             # Потокобезопасность, CRUD
    +-- test_data_analysis.py        # describe, correlation, outliers
    +-- test_utils.py                # Валидация имён
    +-- test_virtual_table_model.py  # pytest-qt, загрузка страниц

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

  Windows 10/11 (x64)    : SQLiteViewer.exe в архиве sqlite-viewer-windows-x64.zip
  Windows 10/11 (x86)    : SQLiteViewer.exe в архиве sqlite-viewer-windows-x86.zip
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
  3. Просмотр данных с поиском, пагинацией, сортировкой
  4. Вкладка "SQL запросы" — редактор, подсветка, автодополнение
  5. Вкладка "Конструктор таблиц" — визуальное редактирование схемы
  6. Вкладка "Графики" — визуализация и отчёт

ГОРЯЧИЕ КЛАВИШИ:
  Ctrl+O          Открыть базу данных
  Ctrl+N          Создать новую БД
  Ctrl+F          Поиск в таблице
  F5 / Ctrl+Enter Выполнить SQL-запрос
  Ctrl+Space      Автодополнение SQL
  Ctrl+Q          Выход

ЦВЕТОВАЯ СХЕМА:
  Основной акцент : красный (#ff4444, #8b0000)
  Выделение       : синий (#003366)
  Фон             : тёмные оттенки (#1a1a1a, #2d2d2d, #0d0d0d)

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

Модуль functions/data_analysis.py (pandas/NumPy) предоставляет:

  * describe(df)                            — описательная статистика
  * null_report(df)                         — отчёт по пропускам
  * correlation(df)                         — матрица корреляций
  * outliers_iqr(df, column)                — выбросы методом IQR
  * group_aggregate(df, group_col, value_col, agg) — группировки
  * full_report(df)                         — сводный отчёт

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
      # или
      python build.py

  Linux (Zorin / Ubuntu / Debian):
      chmod +x build_app.sh
      ./build_app.sh
      # или
      python3 build.py

Результат: dist/SQLiteViewer/SQLiteViewer[.exe].

ЧТО ДЕЛАЕТ build.py:
  1. Устанавливает зависимости из requirements.txt и PyInstaller.
  2. Очищает build/ и dist/.
  3. Запускает PyInstaller с SQLiteViewer.spec.
  4. Копирует папку icons/ в сборку.
  5. Печатает путь к готовому бинарнику.

GITHUB ACTIONS:
Файл .github/workflows/build.yml содержит три job'а:

  Job              Матрица             Артефакты
  ---------------  ------------------  ------------------------------
  build-linux      appimage, deb       .AppImage, .deb
  build-windows    x64, x86            папка dist/SQLiteViewer/
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
  sqlite-viewer-windows-x64.zip
  sqlite-viewer-windows-x86.zip

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
  * Для x86-сборки в CI используется architecture: x86 в setup-python.
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
  * test_data_analysis.py         — describe, correlation, outliers, group_aggregate
  * test_utils.py                 — валидация имён таблиц/колонок
  * test_virtual_table_model.py   — загрузка страниц (pytest-qt)

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
  [x] Множественные вкладки запросов
  [x] Экспорт в PDF
  [x] EXPLAIN QUERY PLAN
  [x] Подсветка синтаксиса
  [x] Визуальный редактор таблиц
  [x] Постраничная загрузка данных
  [x] Добавление/удаление строк и колонок
  [x] Графики и визуализация
  [x] Аналитика (pandas / NumPy)
  [x] CI/CD (Windows x64/x86, Linux AppImage + .deb)
  [x] Кроссплатформенные логи и история запросов
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