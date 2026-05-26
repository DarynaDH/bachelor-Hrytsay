# Telegram-бот з інтеграцією методів штучного інтелекту для підтримки користувачів і аналітики ігрового сервера

**Кваліфікаційна робота бакалавра**  
ПЗВО «ІТ СТЕП Університет», 2026

**Автор:** Грицай Дарина Павлівна, група 4CS-43, спеціальність 122 «Комп'ютерні науки»

**Науковий керівник:** Колдовський В'ячеслав Васильович, кандидат економічних наук, доцент, керівник компетентностей SoftServe Academy


## Короткий опис проєкту

Telegram-бот з інтеграцією великих мовних моделей (LLM) для:
- автоматизованої підтримки користувачів ігрового сервера GTA RP
- збору і аналізу подій активності гравців
- генерації аналітичних звітів через AI (GPT-5.4 як основна модель, Qwen3.5-397B як резервна)
- веб-інтерфейсу адміністратора з графіками активності

### Стек технологій

- **Backend:** Python 3.11, FastAPI, psycopg2
- **Telegram-бот:** aiogram 3.x
- **База даних:** PostgreSQL 16 (Docker)
- **AI-інтеграція:** OpenRouter API
- **Веб-інтерфейс:** HTML/CSS/JavaScript + Chart.js
- **Excel-звіти:** openpyxl

## Передумови

Для запуску потрібно встановити:

- **Python 3.11+** ([python.org](https://www.python.org/downloads/))
- **Docker Desktop** ([docker.com](https://www.docker.com/products/docker-desktop/))
- **Telegram Bot Token** — отримати у [@BotFather](https://t.me/BotFather)
- **OpenRouter API key** — зареєструватись на [openrouter.ai](https://openrouter.ai)

## Встановлення та запуск (Windows)

### 1. Клонування репозиторію
```bash
git clone https://github.com/DarynaDH/bachelor-Hrytsai.git
cd bachelor-Hrytsai
```
### 2. Налаштування конфігурації
Скопіювати файл `.env.example` у `.env`:
```bash
copy .env.example .env
```
Відкрити `.env` будь-яким текстовим редактором і заповнити власні значення:
BOT_TOKEN=токен_отриманий_у_BotFather
OPENROUTER_API_KEY=ключ_з_openrouter.ai
ADMIN_IDS=ваш_telegram_user_id
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gamebot
DB_USER=postgres
DB_PASSWORD=postgres
> **Як дізнатись свій Telegram user ID:** написати боту [@userinfobot](https://t.me/userinfobot) — він поверне ваш ID.

### 3. Створення віртуальних середовищ і встановлення залежностей

**Для backend:**

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
deactivate
cd ..
```

**Для бота:**

```bash
cd bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
deactivate
cd ..
```

### 4. Запуск системи

Перед запуском переконатись що **Docker Desktop запущений**.

Послідовно запустити (кожен .bat у новому вікні):

1. `start_db.bat` — запускає PostgreSQL у Docker. Зачекати 5–10 секунд поки БД підніметься.
2. `seed.bat` — наповнити базу даних демонстраційними подіями (опціонально, рекомендовано для перевірки).
3. `start_backend.bat` — запускає FastAPI сервер на `http://localhost:8000`
4. `start_bot.bat` — запускає Telegram-бота

### 5. Перевірка роботи

- **Веб-інтерфейс адміністратора:** відкрити в браузері `http://localhost:8000`
- **Telegram-бот:** написати своєму боту команду `/start`

### 6. Зупинка

Запустити `stop_all.bat` — зупиняє Python-процеси та PostgreSQL-контейнер.

---

## Доступні команди Telegram-бота

| Команда | Доступ | Опис |
|---------|--------|------|
| `/start` | Усі | Привітання і перелік команд |
| `/report` | Усі | Статистика за поточний день |
| `/summary` | Адмін | AI-аналітичний висновок через GPT-5.4 |
| `/table` | Адмін | Excel-звіт з трьома аркушами |
| Будь-який текст | Усі | Відповідь через мовну модель |

---

## Демонстраційні дані

Файл `db/init.sql` містить SQL-схему таблиць `events` та `players`. Скрипт `seed.py` у корені проєкту (запускається через `seed.bat`) наповнює базу демонстраційними подіями для перевірки роботи системи без підключення до реального ігрового сервера.

---

## Контакти

Питання щодо роботи: darynahrytsay26@gmail.com



