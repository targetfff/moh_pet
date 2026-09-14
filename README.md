# MoH

MoH — маркетплейс, разработанный на фреймворке Flask с каталогом товаров, несколькими продавцами для одного товара, пользовательскими ролями, кабинетом продавца, административной модерацией и защищённой аутентификацией.

Проект развивается как backend/full-stack pet project. Основная цель — не только собрать интерфейс интернет-магазина, но и последовательно приблизить приложение к production-архитектуре: модульная структура, нормализованная БД, миграции, PostgreSQL, безопасность, тесты, фоновые задачи, API, очереди событий и CI/CD.

> Статус: active development.

---

## Что уже реализовано

### Каталог

- каталог товаров с постраничной подгрузкой;
- фильтрация по цене;
- фильтрация по продавцам;
- фильтрация по категориям;
- иерархические категории;
- фильтрация по родительской категории с учётом её потомков;
- несколько предложений продавцов для одного товара;
- страница товара с выбором продавца и цены;
- история недавно просмотренных товаров;
- корзина;
- динамический счётчик товаров в корзине;
- рекламные материалы в каталоге;
- оптимизированные WebP-превью для списков товаров.

### Пользователи и роли

В приложении используются три роли:

- `client` — покупатель;
- `vendor` — продавец;
- `admin` — администратор.

Личный кабинет рендерится отдельно в зависимости от роли.

Авторизованные пользователи могут взаимодействовать с каталогом, корзиной и историей просмотров.

Продавцу дополнительно доступны:

- профиль магазина;
- изменение названия магазина;
- изменение логотипа;
- отправка заявки на торговлю существующим товаром;
- предложение нового товара.

Администратор модерирует заявки продавцов и управляет основными сущностями маркетплейса.

### Продавцы и модерация

Реализованы:

- регистрация профиля продавца;
- загрузка логотипа;
- изменение данных магазина;
- заявка продавца на торговлю существующим товаром;
- прикрепление фотографий к заявке;
- предложение нового товара;
- принятие и отклонение заявок администратором;
- создание или обновление `Offer` после одобрения заявки;
- поддержка нескольких продавцов одного товара.

### Администрирование

Admin-раздел включает:

- просмотр товаров с пагинацией;
- CRUD товаров;
- работу с изображениями;
- назначение категорий;
- CRUD категорий;
- CRUD рекламных материалов;
- модерацию заявок на торговлю;
- модерацию предложений новых товаров.

### Аутентификация и безопасность

Реализованы:

- регистрация;
- вход;
- хеширование паролей через Werkzeug;
- server-side валидация email;
- server-side валидация телефона;
- валидация имени;
- password policy;
- нормализация email;
- обязательное подтверждение email;
- повторная отправка письма подтверждения;
- rate limiting auth-endpoints;
- восстановление пароля;
- временные подписанные reset-ссылки;
- инвалидация reset-token после изменения пароля;
- защита от account enumeration;
- CSRF-защита форм;
- CSRF-защита AJAX POST-запросов;
- logout только через `POST`;
- `HttpOnly` session cookie;
- `HttpOnly` remember cookie;
- `SameSite=Lax`;
- configurable `Secure` cookies;
- `strong` session protection Flask-Login;
- безопасная обработка `next` redirect.

Письма сейчас отправляются через SMTP в фоновом `ThreadPoolExecutor`, поэтому HTTP-запрос регистрации, восстановления пароля или повторной отправки подтверждения не блокируется ожиданием SMTP.

---

## База данных

Основная development DB — PostgreSQL.

Для работы используются:

- SQLAlchemy ORM;
- Flask-SQLAlchemy;
- PostgreSQL;
- psycopg 3;
- Flask-Migrate;
- Alembic.

Все изменения структуры БД проходят через Alembic migrations.

### Основные сущности

- `Users`;
- `Vendors`;
- `Products`;
- `Categories`;
- `Offers`;
- `Requests`;
- `Suggestions`;
- `Advertisement`;
- `CartItem`;
- `RecentView`.

Связь Product ↔ Category реализована через many-to-many таблицу product_categories.

Корзина и история просмотров также хранятся в отдельных нормализованных таблицах.

---

## Demo bootstrap

Для проекта есть воспроизводимый bootstrap:

```bash
python scripts/bootstrap_db.py
```

Bootstrap создаёт тестовые аккаунты разных ролей, продавцов, категории, товары, предложения продавцов, заявки на модерацию и рекламный материал.

Bootstrap является идемпотентным: повторный запуск обновляет demo-данные вместо создания дубликатов.

Учетные данные демо-аккаунтов выводятся в консоль после выполнения скрипта.

### Полная инициализация новой БД

Для чистой PostgreSQL последовательность выглядит так:

```bash
flask --app run.py db upgrade
python scripts/bootstrap_db.py
python run.py
```

---

## Дополнительная генерация demo-товаров

Для нагрузочной и визуальной проверки каталога существует отдельный генератор:

```bash
python scripts/generate_demo_products.py --help
```

Например:

```bash
python scripts/generate_demo_products.py --count 40
```

Удаление товаров, созданных этим генератором:

```bash
python scripts/generate_demo_products.py --clean
```

Этот скрипт предназначен для дополнительного наполнения каталога и не заменяет основной `bootstrap_db.py`.

---

## Изображения

Для карточек каталога используются оптимизированные WebP-превью, а для детального просмотра — изображения большего разрешения.

В дальнейшем media storage будет отделён от Flask static-файлов.

---

## Производительность

В проекте есть middleware для измерения производительности HTTP-запросов и SQL.

Пример:

```text
[PERF] GET /account | status=200 | queries=3 | sql=10.08 ms | total=14.32 ms
```

Измеряются:

- число SQL-запросов;
- суммарное SQL-время;
- полное время обработки HTTP-запроса.

Включение:

```env
PERFORMANCE_LOGGING=true
```

В процессе оптимизации отдельно устранялись:

- N+1 запросы;
- лишние `COUNT`;
- лишние `UPDATE`;
- повторные SQL-запросы;
- загрузка тяжёлых оригинальных изображений в карточках каталога.

---

## Тесты

Сейчас автоматическими тестами покрыты основные auth/security сценарии:

- регистрация;
- валидация пароля;
- нормализация email;
- ограничение неподтверждённого аккаунта;
- password reset;
- защита от account enumeration;
- CSRF без токена → `400`;
- CSRF с токеном → запрос проходит;
- `GET /logout` → `405`;
- `POST /logout` завершает сессию;
- session cookie имеет `HttpOnly`;
- session cookie имеет `SameSite=Lax`.

Запуск:

```bash
python -m pytest -vv
```

---

## Архитектура

Приложение построено через Flask Application Factory и Blueprints.

```text
moh_pet/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── performance.py
│   │
│   ├── auth/
│   ├── catalog/
│   ├── account/
│   ├── seller/
│   ├── admin/
│   ├── legit/
│   │
│   ├── models/
│   │
│   └── services/
│       ├── ads.py
│       ├── catalog.py
│       ├── email.py
│       └── images.py
│
├── migrations/
│   ├── versions/
│   ├── env.py
│   ├── alembic.ini
│   └── script.py.mako
│
├── templates/
│   ├── account/
│   ├── admin/
│   ├── auth/
│   ├── catalog/
│   ├── email/
│   ├── includes/
│   ├── legit/
│   └── seller/
│
├── static/
│   ├── css/
│   │   ├── components/
│   │   └── pages/
│   │
│   ├── js/
│   │   ├── components/
│   │   └── pages/
│   │
│   ├── img/
│   └── ads/
│
├── scripts/
│   ├── bootstrap_db.py
│   ├── generate_demo_products.py
│   └── generate_thumbnails.py
│
├── tests/
│   ├── auth/
│   ├── security/
│   └── conftest.py
│
├── .env.example
├── config.py
├── requirements.txt
└── run.py
```

---

## Стек

### Backend

- Python;
- Flask 3;
- Flask-SQLAlchemy;
- SQLAlchemy;
- Flask-Migrate;
- Alembic;
- Flask-Login;
- Flask-WTF / CSRFProtect;
- Flask-Limiter;
- Flask-Mail;
- Werkzeug;
- itsdangerous;
- email-validator;
- Pillow.

### Database

- PostgreSQL;
- psycopg 3.

### Frontend

- Jinja2;
- HTML;
- CSS;
- JavaScript;
- Bootstrap;
- Font Awesome.

### Development

- uv;
- pytest;
- Git;
- Alembic migrations;
- `.env` configuration.

---

# Локальный запуск

Клонирование:

```bash
git clone https://github.com/targetfff/moh_pet.git
cd moh_pet
```

Создание окружения:

```bash
uv venv
```

Windows / Git Bash:

```bash
source .venv/Scripts/activate
```

Установка зависимостей:

```bash
uv pip install -r requirements.txt
```

Подключение под postgres:

```bash
psql -U postgres -d postgres
```

Создание пользователя:

```sql
CREATE USER moh_app WITH PASSWORD 'your-local-password';
```

Создание БД:

```sql
CREATE DATABASE moh OWNER moh_app;
```

Выход:

```sql
\q
```

Создайте локальный `.env`:

```bash
cp .env.example .env
```

Пример:

```env
# Application
SECRET_KEY=replace-with-random-secret
SECURITY_PASSWORD_SALT=replace-with-random-salt
SECURITY_PASSWORD_RESET_SALT=replace-with-another-random-salt

# Database
DATABASE_URL=postgresql+psycopg://moh_app:your-local-password@localhost:5432/moh

# Auth
PASSWORD_RESET_MAX_AGE=3600
EMAIL_CONFIRMATION_MAX_AGE=86400

# SMTP
MAIL_SERVER=smtp.yandex.ru
MAIL_PORT=465
MAIL_USE_TLS=false
MAIL_USE_SSL=true
MAIL_USERNAME=your_mail@example.com
MAIL_PASSWORD=your_smtp_app_password
MAIL_DEFAULT_SENDER=your_mail@example.com

# Rate limiting
RATELIMIT_STORAGE_URI=memory://

# Advertisement
AD_INTERVAL_SECONDS=1800

# Performance logging
PERFORMANCE_LOGGING=false

# false for local HTTP
# true for production HTTPS
COOKIE_SECURE=false
```

Применение migrations

```bash
flask --app run.py db upgrade
```

Проверка:

```bash
flask --app run.py db current
```

Создание demo-данных

```bash
python scripts/bootstrap_db.py
```

Запуск тестов

```bash
python -m pytest -vv
```

Запуск приложения

```bash
python run.py
```

Development server:

```text
http://127.0.0.1:5000
```

---

# Конфигурация

Основные environment variables:

| Variable | Назначение |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask session signing |
| `SECURITY_PASSWORD_SALT` | signing salt |
| `SECURITY_PASSWORD_RESET_SALT` | password reset signing salt |
| `PASSWORD_RESET_MAX_AGE` | срок жизни reset-token |
| `EMAIL_CONFIRMATION_MAX_AGE` | срок жизни confirmation token |
| `MAIL_SERVER` | SMTP server |
| `MAIL_PORT` | SMTP port |
| `MAIL_USE_TLS` | STARTTLS |
| `MAIL_USE_SSL` | SMTP over SSL |
| `MAIL_USERNAME` | SMTP username |
| `MAIL_PASSWORD` | SMTP app password |
| `MAIL_DEFAULT_SENDER` | sender address |
| `RATELIMIT_STORAGE_URI` | Flask-Limiter storage |
| `AD_INTERVAL_SECONDS` | период показа рекламы |
| `PERFORMANCE_LOGGING` | SQL/HTTP performance logs |
| `COOKIE_SECURE` | Secure cookie flag |

---

# Roadmap

Ближайшие этапы развития проекта:

1. **Commerce model** — разделение избранного и корзины, привязка покупок к конкретным предложениям продавцов, заказы и mock payment flow.
2. **Docker Compose** — воспроизводимый запуск Flask, PostgreSQL, Redis и Celery.
3. **GitHub Actions** — автоматический запуск тестов, lint и проверка миграций.
4. **Redis + Celery** — фоновые задачи и асинхронная отправка email.
5. **Search** — полноценный поиск по каталогу.
6. **REST API + OpenAPI + JWT** — внешний программный интерфейс и документированная API-аутентификация.
7. **Kafka** — event-driven взаимодействие для commerce и loyalty-сценариев.
8. **Object Storage** — хранение пользовательских media вне файловой системы приложения.
9. **Observability** — централизованный сбор ошибок, метрик и трассировки.

---
