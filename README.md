![Heritage Bar](/public/img/logo_negate.png)

# Учебный сайт вымышленного бара "Наследие"

## Ссылка на сайт (может временно не работать):
[https://heritagebar-production.up.railway.app/](https://heritagebar-production.up.railway.app/)

## Тестовый аккаунт для входа:
* **Логин:** `laffpie@mail.ru`
* **Пароль:** `popochka_muravia`

---

## Основной стек и функционал:
Fullstack CRUD-приложение бара «Наследие» с серверным рендерингом страниц и полным циклом аутентификации.

* **Backend:** Node.js, Express, EJS (шаблонизатор).
* **База данных:** PostgreSQL (3 таблицы: пользователи, забронированные столики, сессии через `connect-pg-simple`).
* **Безопасность и сессии:** `bcrypt`, `express-session`, `helmet`, подтверждение регистрации через email `nodemailer`.
* **Инфраструктура:** Docker, Docker Compose (автоматическая инициализация базы и live-reload бекенда).
* **Тестирование:** Автоматизированные интеграционные тесты API на Python (`pytest`, `requests`).

---

## Быстрый запуск через Docker (Рекомендуемый способ)

Для запуска требуются только установленные **Docker** и **Docker Compose**. Локально ставить Node.js и PostgreSQL не требуется.

1. Склонировать репозиторий и перейти в папку проекта:
   ```bash
   git clone <URL_РЕПОЗИТОРИЯ>
   cd HeritageBar
   ```

2. Создать файл `.env` в корне проекта (по шаблону переменных ниже)

3. Запустить весь стек одной командой:
   ```bash
   docker compose up --build -d
   ```
   *Docker Compose автоматически поднимет контейнер PostgreSQL, выполнит первичную инициализацию таблиц из `db_init.sql`, дождется статуса `healthy` базы и запустит веб-приложение на порту 3000*

4. Сайт доступен по адресу: `http://localhost:3000`

---

## Ручной запуск (Локальное окружение)

Если вы хотите запустить проект напрямую на хост-машине:

1. Установить зависимости:
   ```bash
   npm install
   ```

2. Развернуть PostgreSQL и инициализировать структуру таблиц скриптом:
   ```bash
   psql -U <db_user> -d <database_name> -f db_init.sql
   ```

3. Настроить файл `.env` и запустить сервер:
   ```bash
   # Для разработки (с автоперезапуском через nodemon):
   npm run devStart

   # Обычный запуск:
   npm start
   ```

---

## Переменные окружения `.env`

Создайте файл `.env` в корневой папке со следующими параметрами:

```env
PORT=3000
BASE_URL=http://localhost:3000

# Настройки подключения к PostgreSQL
DB_USER=postgres
DB_PASS=secret_heritage
DATABASE=heritagebar
DB_PORT=5432
# При запуске через Docker Compose используйте: DB_HOST=db
# При локальном запуске на хосте используйте: DB_HOST=localhost
DB_HOST=db

# Настройки почтового сервиса (nodemailer)
EMAIL_USER=your_email@mail.ru
EMAIL_PASS=your_app_password

# Данные тестового пользователя (для сидов/тестов)
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=Password123!
```

---

## Запуск автотестов (Pytest)

Интеграционные тесты API бэкенда написаны на Python:

```bash
# Активировать виртуальное окружение (находясь в корне проекта)
source .venv/bin/activate  # Для Linux/macOS
# .venv\Scripts\activate   # Для Windows

# Установить зависимости тестирования
pip install -r requirements.txt

# Запустить тесты
pytest -v

# Выйти из виртуального окружения, если понадобится
deactivate
```

---

## Беклог задач:
* [x] Контейнеризация приложения и базы данных (Docker Compose)
* [x] Написание базового набора интеграционных автотестов API бэкенда
* [ ] Повысить покрытие автотестами и исправить выявленные баги бизнес-логики
* [ ] Написать UI/E2E автотесты (на Playwright)
* [ ] Личный кабинет: редактирование профиля и смена пароля
* [ ] Добавить сценарий восстановления забытого пароля по почте
* [ ] Кастомные страницы обработки ошибок (4XX, 5XX)
* [ ] Добавить CSRF-токены
