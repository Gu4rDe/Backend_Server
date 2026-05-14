# Инструкция по настройке сервера с бэкендом

## Содержание

1. [Требования](#1-требования)
2. [Подготовка сервера](#2-подготовка-сервера)
3. [Развёртывание бэкенда](#3-развёртывание-бэкенда)
4. [Настройка systemd service](#4-настройка-systemd-service)
5. [Получение SSL-сертификата Let's Encrypt](#5-получение-ssl-сертификата-lets-encrypt)
6. [Настройка Nginx (reverse proxy)](#6-настройка-nginx-reverse-proxy)
7. [Настройка firewall (ufw)](#7-настройка-firewall-ufw)
8. [Настройка фронтенда на клиентских машинах](#8-настройка-фронтенда-на-клиентских-машинах)
9. [Проверка работы](#9-проверка-работы)
10. [Переход на PostgreSQL](#10-переход-на-postgresql)
11. [Локальная разработка](#11-локальная-разработка)

---

## 1. Требования

- **Сервер:** Ubuntu 22.04+ с root доступом
- **Домен:** Зарегистрированное доменное имя (например, `face-api.example.com`), привязанное к IP сервера через A-запись
- **Python:** 3.10+
- **Порты:** 80 и 443 должны быть свободны и доступны извне

### Что уже есть в проекте

```
Project/
├── backend/              # FastAPI приложение
│   ├── app/
│   │   ├── main.py      # FastAPI приложение
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── services/
│   ├── pyproject.toml   # Зависимости бэкенда
│   └── .env             # Конфигурация
└── frontend/            # Desktop приложение
    ├── core/
    │   └── api_client.py
    ├── ui/
    └── .env             # API_BASE_URL
```

---

## 2. Подготовка сервера

### Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### Установка системных зависимостей

```bash
sudo apt install -y \
    python3.10-venv \
    python3-pip \
    build-essential \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1
```

> **Примечание:** Версия Python может отличаться. Проверьте установленную: `python3 --version`

---

## 3. Развёртывание бэкенда

### Создание пользователя для приложения

```bash
sudo useradd -r -m -s /bin/bash faceapi
```

### Копирование проекта на сервер

```bash
# Скопируйте backend и frontend на сервер
sudo mkdir -p /opt/faceapi
sudo cp -r backend /opt/faceapi/
sudo cp -r frontend /opt/faceapi/
sudo chown -R faceapi:faceapi /opt/faceapi
```

### Создание виртуального окружения

```bash
sudo -u faceapi python3 -m venv /opt/faceapi/backend/.venv
```

### Установка зависимостей

```bash
sudo -u faceapi /opt/faceapi/backend/.venv/bin/pip install --upgrade pip
sudo -u faceapi /opt/faceapi/backend/.venv/bin/pip install \
    bcrypt==4.0.1 \
    "fastapi>=0.110.0" \
    "insightface>=0.7.3" \
    numpy==1.26.4 \
    "onnx>=1.16.0,<1.17" \
    "onnxruntime>=1.16.0,<1.24" \
    opencv-python-headless \
    "passlib[bcrypt]==1.7.4" \
    "pydantic>=2.0,<3.0" \
    python-dotenv==1.0.0 \
    "python-jose[cryptography]==3.3.0" \
    "python-multipart>=0.0.18" \
    sqlalchemy==2.0.23 \
    "uvicorn[standard]==0.24.0"
```

### Настройка .env

```bash
sudo -u faceapi nano /opt/faceapi/backend/.env
```

```env
DATABASE_URL=sqlite:///./data/faces.db
SECRET_KEY=сгенерируйте_случайную_строку_минимум_32_символа
CORS_ORIGINS=https://your-domain.com
```

> **Важно:** Замените `your-domain.com` на ваш реальный домен. Для `SECRET_KEY` сгенерируйте случайную строку: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### Создание директории для данных

```bash
sudo -u faceapi mkdir -p /opt/faceapi/backend/data
```

### Загрузка моделей распознавания лиц

Модели insightface (buffalo_l) скачиваются автоматически при первом запуске (~32 MB).

Для ручной предзагрузки:
```bash
sudo -u faceapi /opt/faceapi/backend/.venv/bin/python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l'); app.prepare(ctx_id=-1)"
```

Для использования AdaFace IR-101 (опционально):
```bash
cd /opt/faceapi/backend
sudo -u faceapi .venv/bin/python scripts/convert_adaface_to_onnx.py
```

Подробнее о моделях см. [MODELS.md](MODELS.md).

---

## 4. Настройка systemd service

### Создание unit-файла

```bash
sudo nano /etc/systemd/system/faceapi.service
```

```ini
[Unit]
Description=Face Recognition API
After=network.target

[Service]
Type=simple
User=faceapi
Group=faceapi
WorkingDirectory=/opt/faceapi/backend
Environment="PATH=/opt/faceapi/backend/.venv/bin"
ExecStart=/opt/faceapi/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=faceapi

[Install]
WantedBy=multi-user.target
```

> **Примечание:** Uvicorn запускается на `127.0.0.1:8000` — доступ только локально. Nginx будет проксировать внешние запросы.

### Активация и запуск

```bash
sudo systemctl daemon-reload
sudo systemctl enable faceapi
sudo systemctl start faceapi
```

### Проверка статуса

```bash
sudo systemctl status faceapi
```

### Просмотр логов

```bash
sudo journalctl -u faceapi -f
```

---

## 5. Получение SSL-сертификата Let's Encrypt

### Установка Certbot

```bash
sudo apt install -y certbot
```

### Остановка Nginx (если уже запущен)

```bash
sudo systemctl stop nginx 2>/dev/null || true
```

### Временная остановка faceapi (для standalone mode на порту 80)

```bash
sudo systemctl stop faceapi
```

### Получение сертификата

```bash
sudo certbot certonly --standalone \
    -d your-domain.com \
    --email your-email@example.com \
    --agree-tos \
    --non-interactive
```

> **Важно:** Замените `your-domain.com` и `your-email@example.com` на ваши данные.

Сертификаты будут сохранены в:
- `/etc/letsencrypt/live/your-domain.com/fullchain.pem`
- `/etc/letsencrypt/live/your-domain.com/privkey.pem`

### Возврат сервисов

```bash
sudo systemctl start faceapi
```

### Настройка автообновления

Certbot автоматически создаёт systemd timer для обновления. Проверьте:

```bash
sudo systemctl status certbot.timer
```

Для ручного обновления:

```bash
sudo certbot renew --dry-run
```

> **Примечание:** После обновления сертификата Nginx нужно перезагрузить: `sudo systemctl reload nginx`

---

## 6. Настройка Nginx (reverse proxy)

### Установка Nginx

```bash
sudo apt install -y nginx
```

### Создание конфигурации

```bash
sudo nano /etc/nginx/sites-available/faceapi
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

> **Важно:** Замените `your-domain.com` на ваш реальный домен.

### Активация конфигурации

```bash
sudo ln -s /etc/nginx/sites-available/faceapi /etc/nginx/sites-enabled/faceapi
sudo rm -f /etc/nginx/sites-enabled/default
```

### Создание директории для Certbot

```bash
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot
```

### Проверка и перезапуск Nginx

```bash
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl reload nginx
```

### Автоматическая перезагрузка Nginx после обновления сертификата

```bash
sudo nano /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

```bash
#!/bin/bash
systemctl reload nginx
```

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

---

## 7. Настройка firewall (ufw)

### Проверка статуса

```bash
sudo ufw status
```

### Настройка правил

```bash
sudo ufw allow 22/tcp comment "SSH"
sudo ufw allow 80/tcp comment "HTTP"
sudo ufw allow 443/tcp comment "HTTPS"
```

### Включение firewall

```bash
sudo ufw enable
```

### Проверка

```bash
sudo ufw status verbose
```

Ожидаемый результат:
```
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere
80/tcp                     ALLOW IN    Anywhere
443/tcp                    ALLOW IN    Anywhere
```

---

## 8. Настройка фронтенда на клиентских машинах

На каждой клиентской машине, где установлен `frontend`:

### Шаг 1: Обновите .env

Создайте или отредактируйте файл `frontend/.env`:

```env
API_BASE_URL=https://your-domain.com
```

### Шаг 2: Запустите приложение

```bash
cd frontend
uv sync
uv run python main.py
```

> **Примечание:** Для HTTPS подключения убедитесь что на сервере настроен валидный SSL-сертификат.

---

## 9. Проверка работы

### Health check

```bash
curl https://your-domain.com/health
```

Ожидаемый ответ:
```json
{"status":"healthy","service":"face-recognition-api","version":"5.0.0"}
```

### Проверка основного эндпоинта

```bash
curl https://your-domain.com/
```

Ожидаемый ответ:
```json
{"message":"Face Recognition API is running"}
```

### Проверка HTTP → HTTPS редиректа

```bash
curl -I http://your-domain.com
```

Ожидаемый ответ: `HTTP/1.1 301 Moved Permanently` с заголовком `Location: https://your-domain.com/`

### Проверка SSL

```bash
curl -vI https://your-domain.com 2>&1 | grep -E "SSL|subject|expire"
```

Или через онлайн-сервис: [SSL Labs](https://www.ssllabs.com/ssltest/)

### Проверка фронтенда

Запустите `frontend` на клиентской машине и проверьте:
- Подключение к серверу (health check должен проходить)
- Авторизация администратора
- Регистрация сотрудника
- Распознавание лица

---

## 10. Переход на PostgreSQL

> **Примечание:** Текущая конфигурация использует SQLite. Этот раздел описывает подготовку к переходу на PostgreSQL для продакшена.

### Установка PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
```

### Создание пользователя и базы данных

```bash
sudo -u postgres psql
```

```sql
CREATE USER faceapi WITH PASSWORD 'ваш_надёжный_пароль';
CREATE DATABASE faceapi_db OWNER faceapi;
ALTER ROLE faceapi SET client_encoding TO 'utf8';
ALTER ROLE faceapi SET default_transaction_isolation TO 'read committed';
ALTER ROLE faceapi SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE faceapi_db TO faceapi;
\q
```

### Установка Python-драйвера

```bash
sudo -u faceapi /opt/faceapi/backend/.venv/bin/pip install psycopg2-binary
```

### Обновление .env

```bash
sudo -u faceapi nano /opt/faceapi/backend/.env
```

```env
# Было (SQLite):
# DATABASE_URL=sqlite:///./data/faces.db

# Стало (PostgreSQL):
DATABASE_URL=postgresql://faceapi:ваш_надёжный_пароль@localhost:5432/faceapi_db
SECRET_KEY=ваш_секретный_ключ
CORS_ORIGINS=https://your-domain.com
```

### Миграция данных из SQLite (опционально)

Если в SQLite уже есть данные, их можно перенести:

```bash
# 1. Экспорт из SQLite
sudo -u faceapi /opt/faceapi/backend/.venv/bin/python3 -c "
import sqlite3
import json

conn = sqlite3.connect('/opt/faceapi/backend/data/faces.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Экспорт admins
cursor.execute('SELECT * FROM admins')
admins = [dict(row) for row in cursor.fetchall()]

# Экспорт employees
cursor.execute('SELECT * FROM employees')
employees = [dict(row) for row in cursor.fetchall()]

with open('/tmp/db_export.json', 'w') as f:
    json.dump({'admins': admins, 'employees': employees}, f)

conn.close()
print('Data exported to /tmp/db_export.json')
"

# 2. Импорт в PostgreSQL (требует написания скрипта под вашу схему)
```

### Перезапуск сервиса

```bash
sudo systemctl restart faceapi
sudo journalctl -u faceapi -f
```

---

## 11. Локальная разработка

Для локальной разработки без публичного домена используйте **mkcert** вместо Let's Encrypt.

### Установка mkcert

```bash
# macOS
brew install mkcert
brew install nss

# Windows
choco install mkcert

# Linux
sudo apt install libnss3-tools
curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
chmod +x mkcert-v*-linux-amd64
sudo cp mkcert-v*-linux-amd64 /usr/local/bin/mkcert
```

### Создание локального CA

```bash
mkcert -install
```

### Генерация сертификата для localhost

```bash
mkdir -p certs
mkcert -key-file certs/key.pem -cert-file certs/cert.pem localhost 127.0.0.1 ::1
```

### Запуск uvicorn с SSL

```bash
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-certfile certs/cert.pem \
    --ssl-keyfile certs/key.pem \
    --reload
```

### Настройка фронтенда для локальной разработки

```env
# frontend/.env
API_BASE_URL="https://localhost:8000"
```

> **Преимущество mkcert:** Сертификат доверенный, `verify=False` в HTTP клиенте не нужен.

---

## Быстрые команды

```bash
# Статус сервисов
sudo systemctl status faceapi nginx

# Логи бэкенда
sudo journalctl -u faceapi -f

# Перезапуск после изменений
sudo systemctl restart faceapi
sudo systemctl reload nginx

# Обновление сертификатов
sudo certbot renew

# Проверка конфигурации Nginx
sudo nginx -t
```
