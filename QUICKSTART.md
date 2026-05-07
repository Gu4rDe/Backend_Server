# Запуск Backend_Server (Miit_FaceDetect) — Краткое руководство

> **Условия:** сервер на Ubuntu 22.04+, домен уже привязан к IP через DuckDNS или другой сервис.
>
> В данном примере: сервер `89.108.78.223`, домен `checkfaceapi-ten.duckdns.org`

---

## Шаг 1 — Подключиться к серверу

```bash
ssh user@89.108.78.223
```

---

## Шаг 2 — Установить Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

---

## Шаг 3 — Клонировать репозиторий

```bash
git clone https://github.com/Gu4rDe/Backend_Server.git
cd Backend_Server/backend
```

---

## Шаг 4 — Исправить entrypoint.sh

> ⚠️ Обязательный шаг — без него контейнер не запустится.

```bash
chmod +x entrypoint.sh
sed -i 's|exec .venv/bin/uvicorn|exec .venv/bin/python -m uvicorn|' entrypoint.sh
```

---

## Шаг 5 — Собрать и запустить контейнер

```bash
docker compose up -d --build
```

---

## Шаг 6 — Задать секреты в .env

```bash
docker compose exec api bash -c "
  SECRET_KEY=\$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
  INVITE_CODE=\$(python -c 'import secrets; print(secrets.token_urlsafe(16))')
  sed -i \"s|^SECRET_KEY=.*|SECRET_KEY=\$SECRET_KEY|\" /app/.env
  sed -i \"s|^INITIAL_INVITE_CODE=.*|INITIAL_INVITE_CODE=\$INVITE_CODE|\" /app/.env
  echo '============================'
  echo 'SECRET_KEY:          '\$SECRET_KEY
  echo 'INITIAL_INVITE_CODE: '\$INVITE_CODE
  echo '============================'
"
```

> ⚠️ **Сохрани `INITIAL_INVITE_CODE`** — он нужен для регистрации первого администратора!

Перезапустить после изменения .env:

```bash
docker compose restart api
```

---

## Шаг 7 — Получить SSL-сертификат

```bash
sudo apt install -y certbot

sudo certbot certonly --standalone \
    -d checkfaceapi-ten.duckdns.org \
    --email your@email.com \
    --agree-tos --non-interactive
```

---

## Шаг 8 — Установить и настроить Nginx

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/faceapi
```

Вставить конфиг:

```nginx
server {
    listen 80;
    server_name checkfaceapi-ten.duckdns.org;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name checkfaceapi-ten.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/checkfaceapi-ten.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/checkfaceapi-ten.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активировать:

```bash
sudo ln -s /etc/nginx/sites-available/faceapi /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx && sudo systemctl restart nginx
```

---

## Шаг 9 — Настроить Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Шаг 10 — Проверить что всё работает

```bash
# По IP (базовая проверка)
curl http://89.108.78.223:8000/health

# По домену с SSL
curl https://checkfaceapi-ten.duckdns.org/health

# Ожидаемый ответ:
# {"status":"healthy","service":"face-recognition-api","version":"3.0.0"}
```

Swagger UI: **https://checkfaceapi-ten.duckdns.org/docs**

---

## Шпаргалка

```bash
docker compose logs -f api          # Логи контейнера
docker compose restart api          # Перезапуск
docker compose down                 # Остановка
docker compose up -d --build        # Пересборка
sudo systemctl reload nginx         # Перезагрузка Nginx
sudo certbot renew                  # Обновить SSL вручную
```
