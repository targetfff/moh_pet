# MoH

MoH — маркетплейс на Flask с каталогом товаров, несколькими продавцами для одного товара, пользовательскими ролями, кабинетом продавца, административной модерацией и защищённой аутентификацией.

Проект развивается как backend/full-stack pet project: основная цель — не только собрать интерфейс магазина, но и последовательно довести приложение до архитектуры, близкой к production: разделённые модули, нормализованная БД, безопасность, тесты, миграции, PostgreSQL, очереди задач, API и CI/CD.

> Статус: active development.

## Что уже реализовано

### Каталог

- каталог товаров с подгрузкой по страницам;
- фильтрация по цене, продавцам и категориям;
- иерархические категории;
- фильтрация по родительской категории с учётом её потомков;
- несколько предложений продавцов для одного товара;
- страница товара с выбором продавца и цены;
- история недавно просмотренных товаров;
- рекламные материалы в каталоге;
- отдельные оптимизированные WebP-превью для списков товаров.

### Пользователи и роли

В приложении используются три роли:

- `client` — покупатель;
- `vendor` — продавец;
- `admin` — администратор.

Личный кабинет рендерится отдельно для каждой роли.

Покупателю доступны история просмотра и работа с корзиной. Продавец может редактировать профиль магазина, отправлять заявку на торговлю существующим товаром и предлагать новый товар. Администратор модерирует заявки и управляет сущностями маркетплейса.

### Продавцы и модерация

Реализованы:

- регистрация профиля продавца;
- загрузка логотипа;
- изменение названия и логотипа магазина;
- заявка продавца на торговлю существующим товаром;
- прикрепление фотографий к заявке;
- предложение нового товара;
- принятие и отклонение заявок администратором;
- создание/обновление `Offer` после одобрения заявки.

### Администрирование

Admin-раздел включает:

- просмотр товаров с пагинацией;
- создание, редактирование и удаление товаров;
- работу с изображениями товара;
- назначение категорий;
- CRUD категорий;
- CRUD рекламных материалов;
- модерацию заявок продавцов;
- модерацию предложений новых товаров.

### Аутентификация и безопасность

Реализованы:

- регистрация и вход;
- хеширование паролей через Werkzeug;
- server-side валидация email, телефона, имени и пароля;
- нормализация email;
- обязательное подтверждение email;
- повторная отправка письма подтверждения с rate limit;
- восстановление пароля по временной подписанной ссылке;
- инвалидация reset-token после изменения пароля;
- защита auth-endpoints через Flask-Limiter;
- CSRF-защита обычных форм и AJAX POST-запросов;
- logout только через `POST`;
- `HttpOnly` session/remember cookies;
- `SameSite=Lax`;
- `Secure` cookies для HTTPS-окружения;
- `strong` session protection Flask-Login;
- generic error при неверном email/пароле без раскрытия существования аккаунта.

Письма отправляются через SMTP в фоновом `ThreadPoolExecutor`, поэтому HTTP-запрос регистрации или повторной отправки письма не блокируется ожиданием SMTP.

## Тесты

Сейчас покрыты основные сценарии auth/security:

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
- session cookie имеет `HttpOnly` и `SameSite=Lax`.

Текущий набор:

```text
12 passed
```

Запуск:

```bash
python -m pytest -vv
```

## Архитектура

Приложение построено через Flask Application Factory и Blueprints.

```text
moh_pet/
├── app/
│   ├── __init__.py          # create_app(), extensions init, common hooks
│   ├── extensions.py        # SQLAlchemy, LoginManager, Mail, Limiter, CSRF
│   ├── performance.py       # SQL/query performance logging
│   │
│   ├── auth/                # registration, login, confirmation, reset
│   ├── catalog/             # catalog, product, cart, filters
│   ├── account/             # role-specific personal accounts
│   ├── seller/              # vendor onboarding and requests
│   ├── admin/               # moderation and CRUD
│   ├── legit/               # Legit Check section
│   │
│   ├── models/              # SQLAlchemy models
│   └── services/
│       ├── ads.py
│       ├── catalog.py
│       ├── email.py
│       └── images.py
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
│   └── js/
│       ├── components/
│       └── pages/
│
├── scripts/
│   ├── generate_demo_products.py
│   └── generate_thumbnails.py
│
├── tests/
│   ├── auth/
│   ├── security/
│   └── conftest.py
│
├── config.py
├── requirements.txt
└── run.py
```

Frontend также разделён по ответственности: общие компоненты вынесены в `templates/includes`, CSS — в `static/css/components` и `static/css/pages`, JS — в `static/js/components` и `static/js/pages`. Большие inline `<style>` и inline executable scripts из шаблонов удалены.

## Модель данных

Основные сущности:

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

Связь `Product ↔ Category` реализована через отдельную many-to-many таблицу `product_categories`.

Корзина и история просмотра также хранятся в нормализованных таблицах, а не в сериализованных полях пользователя.

## Производительность

В проекте есть опциональный middleware для измерения:

- количества SQL-запросов;
- времени выполнения SQL;
- полного времени HTTP-запроса.

Включается через:

```env
PERFORMANCE_LOGGING=true
```

При оптимизации каталога и пользовательских страниц отдельно устранялись N+1-запросы и лишние `COUNT/UPDATE`.

Для каталогов используются уменьшенные WebP thumbnails, а оригинальные изображения остаются доступны на странице товара.

## Стек

**Backend**

- Python
- Flask 3
- Flask-SQLAlchemy
- SQLAlchemy
- Flask-Login
- Flask-WTF / CSRFProtect
- Flask-Limiter
- Flask-Mail
- Werkzeug
- itsdangerous
- email-validator
- Pillow

**Frontend**

- Jinja2
- HTML/CSS
- JavaScript
- Bootstrap
- небольшое количество legacy UI-библиотек, которые постепенно заменяются собственными компонентами

**Storage**

- SQLite — текущая development DB;
- локальные изображения в `static/img`.

## Локальный запуск

### 1. Клонирование

```bash
git clone https://github.com/targetfff/moh_pet.git
cd moh_pet
```

### 2. Окружение через uv

```bash
uv venv
uv pip install -r requirements.txt
```

Для запуска тестов также нужен pytest:

```bash
uv pip install pytest==8.3.5
```

### 3. Переменные окружения

Создай `.env` в корне проекта.

Минимальная конфигурация:

```env
SECRET_KEY=replace-with-random-secret
SECURITY_PASSWORD_SALT=replace-with-random-salt
SECURITY_PASSWORD_RESET_SALT=replace-with-another-random-salt

MAIL_SERVER=smtp.yandex.ru
MAIL_PORT=465
MAIL_USE_TLS=false
MAIL_USE_SSL=true
MAIL_USERNAME=your_mail@example.com
MAIL_PASSWORD=your_smtp_app_password
MAIL_DEFAULT_SENDER=your_mail@example.com

PASSWORD_RESET_MAX_AGE=3600
EMAIL_CONFIRMATION_MAX_AGE=86400

RATELIMIT_STORAGE_URI=memory://
PERFORMANCE_LOGGING=false

# false для локального HTTP.
# В production с HTTPS должно быть true.
COOKIE_SECURE=false
```

### 4. База данных

Текущая development-конфигурация использует:

```text
sqlite:///shop.db
```

Для создания пустой схемы:

```bash
uv run python -c "from app import create_app; from app.extensions import db; app=create_app(); ctx=app.app_context(); ctx.push(); db.create_all(); ctx.pop()"
```

После этого приложение можно запустить, но каталог новой БД будет пустым.

### 5. Запуск приложения

```bash
python run.py
```

Development server:

```text
http://127.0.0.1:5000
```

## Генерация тестовых данных

Если локальная БД уже содержит базовые категории, продавцов и товары, можно добавить demo products:

```bash
uv run python scripts/generate_demo_products.py --help
```

Превью изображений:

```bash
uv run python scripts/generate_thumbnails.py
```

## Roadmap

Ближайшие этапы:

1. Flask-Migrate / Alembic и переход с SQLite на PostgreSQL.
2. Воспроизводимый seed/demo bootstrap.
3. Разделение сохранённых товаров и корзины; привязка cart item к конкретному offer.
4. `Order`, `OrderItem`, `Payment` и mock payment flow.
5. Docker Compose: web + PostgreSQL + Redis + Celery.
6. GitHub Actions: tests/lint.
7. Redis и Celery для фоновых задач и email вместо локального thread pool.
8. Поиск по каталогу.
9. Полный seller moderation flow.
10. Legit Check workflow.
11. REST API `/api/v1`, OpenAPI и JWT для API-клиентов.
12. Kafka-события для commerce/loyalty сценариев.
13. Sentry/OpenTelemetry/Prometheus/Grafana.
14. Object storage для media.
