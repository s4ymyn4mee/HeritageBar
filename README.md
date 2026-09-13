![Heritage Bar](/public/img/logo_negate.png)

# Учебный сайт вымышленного бара "Наследие"

[![Tests & Allure Report](https://github.com/s4ymyn4mee/HeritageBar/actions/workflows/allure.yml/badge.svg)](https://github.com/s4ymyn4mee/HeritageBar/actions/workflows/allure.yml)
[![Tests](https://img.shields.io/badge/Tests-67%20passed-brightgreen?style=flat-square&logo=pytest&logoColor=white)](https://s4ymyn4mee.github.io/HeritageBar/)
[![Allure Report](https://img.shields.io/badge/Allure%20Report-Live%20Dashboard-29C7C8?style=flat-square&logo=allure&logoColor=white)](https://s4ymyn4mee.github.io/HeritageBar/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/s4ymyn4mee/HeritageBar/actions)
[![Hosting](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-222222?style=flat-square&logo=githubpages&logoColor=white)](https://s4ymyn4mee.github.io/HeritageBar/)

<br>

[![Node.js](https://img.shields.io/badge/Node.js-20.x-339933?style=flat-square&logo=nodedotjs&logoColor=white)](#)
[![Express](https://img.shields.io/badge/Express.js-Backend%20SSR-000000?style=flat-square&logo=express&logoColor=white)](#)
[![EJS](https://img.shields.io/badge/EJS-Templates-B4CA65?style=flat-square&logo=ejs&logoColor=black)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Docker%20Compose-Containerized-2496ED?style=flat-square&logo=docker&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-Integration%20Tests-3776AB?style=flat-square&logo=python&logoColor=white)](#)

---

## Интерактивный отчет Allure (GitHub Pages):
Результаты последнего прогона автотестов в CI/CD пайплайне:  
→ **[https://s4ymyn4mee.github.io/HeritageBar/](https://s4ymyn4mee.github.io/HeritageBar/)**

## Ссылка на сайт (может временно не работать):
[https://heritagebar-production.up.railway.app/](https://heritagebar-production.up.railway.app/)

## Тестовый аккаунт для входа:
* **Логин:** `laffpie@mail.ru`
* **Пароль:** `popochka_muravia`

## Основной стек и функционал:
Fullstack CRUD-приложение бара «Наследие» с серверным рендерингом страниц и полным циклом аутентификации.

* **Backend:** Node.js, Express, EJS (шаблонизатор).
* **База данных:** PostgreSQL (3 таблицы: пользователи, забронированные столики, сессии).
* **Безопасность и сессии:** `bcrypt`, `express-session`, `helmet`, подтверждение регистрации через email `nodemailer`.
* **Инфраструктура:** Docker, Docker Compose (автоматическая инициализация базы и изолированный стек).
* **Тестирование:** Автоматизированные интеграционные тесты API на Python (`pytest`, `requests`).
* **CI/CD & Reporting:** GitHub Actions (автоматический прогон сьюта на каждый пуш в `main`), Allure Framework, GitHub Pages.

---

## Быстрый запуск через Docker (Рекомендуемый способ)

Для запуска требуются только установленные **Docker** и **Docker Compose**. Локально ставить Node.js и PostgreSQL не требуется.

1. Склонировать репозиторий и перейти в папку проекта:
   ```bash
   git clone https://github.com/s4ymyn4mee/HeritageBar.git
   cd HeritageBar
   ```

2. Создать файл `.env` в корне проекта (заполнить по шаблону переменных ниже):
   ```bash
   cp .env.example .env
   ```

3. Запустить весь стек одной командой:
   ```bash
   docker compose up --build -d
   ```
   *Docker Compose автоматически поднимет контейнер PostgreSQL, выполнит первичную инициализацию таблиц из `db_init.sql`, дождется статуса `healthy` базы и запустит веб-приложение на порту 3000*

4. Сайт будет доступен по адресу: `http://localhost:3000`

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

## Переменные окружения `.env`

Заполните файл `.env` в корневой папке со следующими параметрами:

```env
PORT=3000
BASE_URL=http://localhost:3000

# Настройки почтового сервиса (nodemailer)
EMAIL_USER=your_email@mail.ru
EMAIL_PASS=your_app_password

# Настройки подключения к PostgreSQL
DB_USER=postgres
DB_PASS=secret_heritage
# При запуске через Docker Compose используйте: DB_HOST=db
# При локальном запуске на хосте используйте: 
DB_HOST=localhost
DB_PORT=5432
DATABASE=heritagebar

# Данные тестового пользователя (для сидов/тестов)
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=Password123!
```

## Автоматизация тестирования (Pytest + Allure)
Сьют из 67 тестов проверяет сценарии авторизации, сессионный менеджмент, санитизацию данных, а также устойчивость к SQL-инъекциям и XSS-атакам.

```bash
# Активировать виртуальное окружение (в корне проекта)
source .venv/bin/activate  # Для Linux/macOS
# .venv\Scripts\activate   # Для Windows

# Установить зависимости тестирования
pip install -r requirements.txt

# Запустить тесты со сбором артефактов Allure
pytest -v --alluredir=allure-results --clean-alluredir

# Сгенерировать и открыть отчет Allure локально в браузере (требуется Allure CLI)
allure serve allure-results

# Выйти из виртуального окружения
deactivate
```

---

## Бэклог задач:
* [x] Контейнеризация приложения и базы данных (Docker Compose)
* [x] Написание базового набора интеграционных автотестов API бэкенда (вся авторизация)
* [x] Добавить автоматическую генерацию отчетов Allure
* [x] Зафиксировать баг-репорты либо в Jira, либо в Github Issues
* [X] Исправить баги на серваке, сделать ре-тесты, закрыть баги в Github Issues (3/3)
* [x] Построить CI/CD пайплайн
* [x] Захостить на Github Pages Allure-отчет, повесить на CI/CD пайплайн
* [ ] Повысить покрытие автотестами (вся регистрация и бронирование столиков)
* [ ] Написать UI/E2E автотесты (на Playwright)
* [ ] Личный кабинет: редактирование профиля и смена пароля
* [ ] Добавить сценарий восстановления забытого пароля по почте
* [ ] Кастомные страницы обработки ошибок (4XX, 5XX)
* [ ] Добавить CSRF-токены
