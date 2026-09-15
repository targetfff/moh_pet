# MoH

MoH — маркетплейс, разработанный на фреймворке Flask с каталогом товаров, несколькими продавцами для одного товара, личными кабинетами покупателей и продавцов, административной модерацией, корзиной, избранным, заказами и mock-платежами.

Проект развивается как backend/full-stack pet project с production-архитектурой: модульное приложение, PostgreSQL, миграции, нормализованная модель данных, security-механизмы, тесты, измерение производительности и дальнейший переход к контейнеризации, фоновой обработке задач, API и очереди событий и CI/CD.

> Статус: active development.

---

## Что уже реализовано

### Каталог

- каталог товаров с постраничной подгрузкой;
- фильтрация по цене, продавцам и категориям;
- иерархические категории;
- фильтрация по родительской категории с учётом её потомков;
- несколько предложений продавцов для одного товара;
- страница товара с выбором продавца и актуальной ценой;
- история недавно просмотренных товаров;
- корзина;
- динамический счётчик товаров в корзине;
- рекламные материалы в каталоге;
- оптимизированные WebP-превью для списков товаров.

### Commerce

Модель покупки разделена на отдельные классы:

- `Favorite` хранит связь пользователя с понравившимся товаром;
- `CartItem` хранит выбранный `Offer` от продавца;
- один товар от разных продавцов создаёт разные позиции корзины;
- количество товара изменяется внутри конкретной позиции корзины;
- денежные значения хранятся через `Numeric(12, 2)` / `Decimal`;
- цена всегда берётся на сервере из предложения продавца.

При создании заказа фиксируются snapshot-данные:

- товар;
- продавец;
- цена за единицу;
- количество;
- стоимость Legit Check;
- итоговая стоимость позиции.

Изменение корзины или предложения продавца после оформления не изменяет уже созданный заказ.

Mock-payment поддерживает успешный и неуспешный сценарии. При успешной оплате из корзины удаляется только фактически купленное количество. При неуспешной оплате корзина сохраняется.

### Личный кабинет

Для покупателя реализованы:

- обзор аккаунта;
- история заказов с их статусами (pending, paid и failed);
- избранное;
- история просмотров;
- динамические счётчики корзины и избранного.

Страница `/orders/<id>` доступна только владельцу заказа.

### Пользователи и роли

В приложении используются три роли:

- `client` — покупатель;
- `vendor` — продавец;
- `admin` — администратор.

Продавцу доступны:

- профиль магазина;
- изменение названия магазина;
- изменение логотипа;
- отправка заявки на торговлю существующим товаром;
- предложение нового товара.

Администратор модерирует заявки продавцов и управляет основными сущностями маркетплейса.

### Продавцы и модерация

Реализованы:

- регистрация профиля продавца;
- загрузка и изменение логотипа;
- изменение данных магазина;
- заявки на торговлю существующим товаром;
- прикрепление фотографий к заявке;
- предложение нового товара;
- принятие и отклонение заявок администратором;
- создание или обновление `Offer` после одобрения заявки;
- поддержка предложений нескольких продавцов для одного товара.

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

- регистрация и вход;
- хеширование паролей через Werkzeug;
- server-side валидация email, телефона и имени;
- password policy;
- нормализация email;
- обязательное подтверждение email;
- повторная отправка письма подтверждения;
- rate limiting auth-endpoints;
- восстановление пароля;
- временные подписанные reset-ссылки;
- инвалидация reset-token после изменения пароля;
- защита от account enumeration;
- CSRF-защита форм и AJAX POST-запросов;
- logout только через `POST`;
- `HttpOnly` session / remember cookies;
- `SameSite=Lax`;
- configurable `Secure` cookies;
- `strong` session protection Flask-Login;
- безопасная обработка `next` redirect.

Письма отправляются через SMTP в фоновом `ThreadPoolExecutor`, чтобы HTTP-запрос не блокировался ожиданием SMTP.

---

## База данных

Основная development DB — PostgreSQL.

Используются:

- SQLAlchemy ORM;
- Flask-SQLAlchemy;
- PostgreSQL;
- psycopg 3;
- Flask-Migrate;
- Alembic.

Изменения структуры БД выполняются только через миграции.

### Основные сущности

- `Users`;
- `Vendors`;
- `Products`;
- `Categories`;
- `Offers`;
- `Favorite`;
- `CartItem`;
- `Order`;
- `OrderItem`;
- `Payment`;
- `Requests`;
- `Suggestions`;
- `Advertisement`;
- `RecentView`.

Связь Product ↔ Category реализована через many-to-many таблицу product_categories.

Commerce-модель строится вокруг серверного `Offer`: корзина ссылается на предложение конкретного продавца, а заказ сохраняет исторический snapshot данных на момент checkout.

---

## Demo bootstrap

Для воспроизводимого наполнения новой БД используется:

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
- повторные SQL-запросы;
- ненужные `UPDATE`;
- загрузка тяжёлых изображений в списках;

---

## Тесты

Автоматическими тестами покрыты auth/security и commerce-сценарии.

Проверяются, в частности:

- регистрация и вход;
- валидация пароля;
- подтверждение email;
- password reset;
- защита от account enumeration;
- CSRF;
- logout и параметры session cookie;
- создание заказа из корзины;
- snapshot `OrderItem`;
- точность денежных расчётов;
- successful / failed mock-payment;
- сохранение корзины при failed payment;
- списание только купленного количества;
- защита чужого `/orders/<id>`;
- повторный success-запрос для уже оплаченного заказа.

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
│   ├── orders/
│   ├── seller/
│   ├── admin/
│   ├── legit/
│   │
│   ├── models/
│   │   ├── order.py
│   │   └── ...
│   │
│   └── services/
│       ├── ads.py
│       ├── catalog.py
│       ├── email.py
│       ├── images.py
│       └── orders.py
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
│   ├── orders/
│   └── seller/
│
├── static/
│   ├── css/
│   │   ├── components/
│   │   └── pages/
│   ├── js/
│   │   ├── components/
│   │   └── pages/
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
│   ├── unit/
│   ├── integration/
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

Подключение к PostgreSQL:

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

Применение migrations:

```bash
flask --app run.py db upgrade
```

Проверка:

```bash
flask --app run.py db current
flask --app run.py db check
```

Создание demo-данных:

```bash
python scripts/bootstrap_db.py
```

Запуск тестов:

```bash
python -m pytest -vv
```

Запуск приложения:

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
| `PERFORMANCE_LOGGING` | performance middleware |
| `COOKIE_SECURE` | Secure cookies для HTTPS |

---

# Roadmap

Ближайшие этапы развития проекта:

1. **Docker Compose** — воспроизводимый запуск Flask, PostgreSQL, Redis и Celery.
2. **GitHub Actions** — автоматический запуск тестов, lint и проверка миграций.
3. **Redis + Celery** — фоновые задачи и асинхронная отправка email.
4. **Search** — полноценный поиск по каталогу.
5. **REST API + OpenAPI + JWT** — внешний программный интерфейс и документированная API-аутентификация.
6. **Kafka + Notifications** — очередь событий для заказов, оплат и модерации; consumer уведомлений будет формировать пользовательские уведомления.
7. **Partial navigation** — переход между разделами личного кабинета через Fetch API + History API без полной перезагрузки страницы.
8. **Object Storage** — хранение пользовательских media вне файловой системы приложения.
9. **Observability** — централизованный сбор ошибок, метрик и трассировки.
---