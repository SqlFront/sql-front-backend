# sql-front-backend

### О проекте

API веб-приложения для решения задач по SQL на тематику Великой Отечественной Войны. Цель проекта – повышение патриотического воспитания у студентов IT-специальностей.

### Используемый стек

* FastAPI
* SQLAlchemy
* PostgreSQL
* JWT, PyJWT
* uvicorn

### Интеграционные тесты с PostgreSQL

Из папки бэкенда запустите отдельный контейнер PostgreSQL 15 и тесты.
Команды для PowerShell при установленном виртуальном окружении с зависимостями
из `requirements-dev.txt`.

```powershell
docker compose -f compose.test.yml up -d --wait
$env:SQLFRONT_TEST_DATABASE_URL = 'postgresql+asyncpg://sqlfront_test:sqlfront_test@127.0.0.1:55432/sqlfront_test'
& .venv/Scripts/python.exe -m pytest -o cache_dir=.pytest_cache -m postgres_integration tests/test_postgres_integration.py -q
```

Тесты проверяют результат запроса с CTE и вывод замечания о стиле, откат
квестового UPDATE и выполнение PL/pgSQL-функции на нескольких входах с откатом.
Без переменной `SQLFRONT_TEST_DATABASE_URL` интеграционные проверки пропускаются.
Контейнер использует отдельный порт и хранит тестовую базу в памяти.

```powershell
docker compose -f compose.test.yml down
Remove-Item Env:SQLFRONT_TEST_DATABASE_URL
```

### Автор
* [Гуров Тимофей](https://github.com/HankyYt) - DE, FullStack

### Авторы прототипа

* [Валерия Таранова](https://github.com/tarvarrs) - backend
* [Екатерина Домашова](https://github.com/katteri) - frontend

