# Развёртывание TURN сервера (coturn) через Docker

Этот мануал описывает как поднять собственный TURN сервер для использования с кастомным клиентом Telegram или любым WebRTC приложением. Сервер обеспечивает проксирование медиатрафика (голос, видео) через NAT и обход блокировок DPI.

---

## Как это работает

TURN (Traversal Using Relays around NAT) — протокол который позволяет двум клиентам обмениваться медиатрафиком через промежуточный сервер когда прямое соединение невозможно. В контексте Telegram звонков:

```
Клиент А (за блокировками) ←→ TURN сервер ←→ Клиент Б
```

Клиент А регистрирует на TURN сервере свой relay-адрес и передаёт его собеседнику через сигнализацию Telegram. Клиент Б подключается к TURN серверу напрямую — и оба говорят через него. SRTP шифрование остаётся end-to-end, TURN сервер видит только зашифрованные пакеты.

---

## Требования

- VPS с публичным IP адресом (рекомендуется: Hetzner, Netcup, OVH)
- Ubuntu 22.04 / 24.04
- Docker и Docker Compose
- Домен с возможностью добавить A-запись
- Открытые порты: `3478/tcp`, `3478/udp`, `5349/tcp`, `5349/udp`, `49152-65535/udp`

> **Важно:** VPS должен быть доступен из России. Рекомендуемые локации: Финляндия, Нидерланды, Германия.

---

## Шаг 1 — Подготовка сервера

```bash
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com | sh

# Устанавливаем certbot для TLS сертификатов
apt install -y certbot iptables-persistent
```

---

## Шаг 2 — DNS запись

У своего регистратора создай A-запись:

```
turn.ваш-домен.com  →  IP_вашего_сервера
```

Подожди несколько минут пока запись разойдётся. Проверить:

```bash
dig +short turn.ваш-домен.com
```

---

## Шаг 3 — TLS сертификат

```bash
# Открываем 80 порт временно для верификации
iptables -I INPUT -p tcp --dport 80 -j ACCEPT

# Получаем сертификат
certbot certonly --standalone \
  --preferred-challenges http \
  -d turn.ваш-домен.com

# Закрываем 80 порт
iptables -D INPUT -p tcp --dport 80 -j ACCEPT

# Открываем права на archive директорию чтобы Docker мог читать симлинки
chmod 755 /etc/letsencrypt/archive/
```

---

## Шаг 4 — Подготовка файлов

```bash
# Создаём структуру директорий
mkdir -p /opt/coturn/{config,certs}

# Копируем сертификаты (реальные файлы, не симлинки)
cp /etc/letsencrypt/archive/turn.ваш-домен.com/fullchain1.pem /opt/coturn/certs/fullchain.pem
cp /etc/letsencrypt/archive/turn.ваш-домен.com/privkey1.pem /opt/coturn/certs/privkey.pem
chmod 644 /opt/coturn/certs/fullchain.pem
chmod 644 /opt/coturn/certs/privkey.pem

# Генерируем случайный секрет для HMAC авторизации
# СОХРАНИ ЭТО ЗНАЧЕНИЕ — оно нужно для Auth API
openssl rand -hex 32
```

---

## Шаг 5 — Конфигурация coturn

Создай файл `/opt/coturn/config/turnserver.conf`:

```bash
cat > /opt/coturn/config/turnserver.conf << 'EOF'
# Порты
listening-port=3478
tls-listening-port=5349

# Публичный IP сервера (замени на свой)
listening-ip=ВАШ_ПУБЛИЧНЫЙ_IP
external-ip=ВАШ_ПУБЛИЧНЫЙ_IP

# Домен
realm=turn.ваш-домен.com
server-name=turn.ваш-домен.com

# TLS сертификаты
cert=/etc/certs/fullchain.pem
pkey=/etc/certs/privkey.pem

# HMAC авторизация (вставь секрет из шага 4)
use-auth-secret
static-auth-secret=ВАШ_СЕКРЕТ_ИЗ_OPENSSL_RAND

# Relay диапазон портов
min-port=49152
max-port=65535

# Безопасность — запрет relay на приватные сети
no-multicast-peers
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=192.168.0.0-192.168.255.255
denied-peer-ip=172.16.0.0-172.31.255.255

# Prometheus метрики
prometheus
prometheus-address=ВАШ_ПУБЛИЧНЫЙ_IP
prometheus-port=9641
prometheus-username-labels

# Логирование
log-file=stdout
verbose
EOF
```

---

## Шаг 6 — Docker Compose

```bash
cat > /opt/coturn/docker-compose.yml << 'EOF'
services:
  coturn:
    image: coturn/coturn:latest
    network_mode: host
    volumes:
      - /opt/coturn/config/turnserver.conf:/etc/coturn/turnserver.conf:ro
      - /opt/coturn/certs:/etc/certs:ro
    restart: unless-stopped
EOF
```

> **Почему `network_mode: host`:** coturn динамически открывает порты из relay диапазона (49152-65535). Через стандартный docker-proxy пробросить 16000+ портов невозможно.

---

## Шаг 7 — Firewall

```bash
# TURN/STUN порты
iptables -A INPUT -p udp --dport 3478 -j ACCEPT
iptables -A INPUT -p tcp --dport 3478 -j ACCEPT
iptables -A INPUT -p udp --dport 5349 -j ACCEPT
iptables -A INPUT -p tcp --dport 5349 -j ACCEPT

# Relay диапазон для медиа
iptables -A INPUT -p udp --dport 49152:65535 -j ACCEPT

# Prometheus метрики (опционально — только если нужен мониторинг)
iptables -A INPUT -p tcp --dport 9641 -j ACCEPT

# Сохраняем правила
netfilter-persistent save
```

---

## Шаг 8 — Запуск

```bash
cd /opt/coturn
docker compose up -d
docker compose logs -f
```

В логах должны появиться строки:

```
INFO: TLS/TCP listener opened on : ВАШ_IP:3478
INFO: TLS/TCP listener opened on : ВАШ_IP:5349
INFO: DTLS/UDP listener opened on: ВАШ_IP:3478
INFO: DTLS/UDP listener opened on: ВАШ_IP:5349
INFO: prometheus exporter server will listen on ВАШ_IP:9641
```

---

## Шаг 9 — Проверка

Установить утилиты для теста:

```bash
# На своём компе (Ubuntu/Debian)
apt install -y coturn
```

Генерируем тестовые credentials и проверяем:

```bash
SECRET="ВАШ_СЕКРЕТ"
TIME=$(date -d "+1 hour" +%s)
USER="$TIME:testuser"
PASS=$(echo -n "$USER" | openssl dgst -binary -sha1 -hmac "$SECRET" | base64)

# Тест TLS (должно показать 0% потерь)
turnutils_uclient -T -u "$USER" -w "$PASS" turn.ваш-домен.com

# Тест STUN (должно вернуть ваш внешний IP)
turnutils_stunclient turn.ваш-домен.com
```

Проверка через браузер — открой https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/ и добавь сервер:

```
URI:      turn:turn.ваш-домен.com:3478
Username: значение USER из команды выше
Password: значение PASS из команды выше
```

После нажатия **Gather candidates** должен появиться кандидат типа `relay`.

---

## Шаг 10 — Автообновление сертификата

Создай хук который копирует новый сертификат и перезапускает coturn:

```bash
cat > /etc/letsencrypt/renewal-hooks/deploy/coturn.sh << 'EOF'
#!/bin/bash
DOMAIN="turn.ваш-домен.com"
cp /etc/letsencrypt/archive/${DOMAIN}/fullchain1.pem /opt/coturn/certs/fullchain.pem
cp /etc/letsencrypt/archive/${DOMAIN}/privkey1.pem /opt/coturn/certs/privkey.pem
chmod 644 /opt/coturn/certs/fullchain.pem
chmod 644 /opt/coturn/certs/privkey.pem
docker compose -f /opt/coturn/docker-compose.yml restart
EOF

chmod +x /etc/letsencrypt/renewal-hooks/deploy/coturn.sh
```

Проверка автообновления:

```bash
certbot renew --dry-run
```

---

## Регистрация сервера в сети

После того как сервер поднят и проверен — зарегистрируй его в централизованном API чтобы все пользователи кастомного клиента могли его использовать.

Для регистрации нужно:

- Публичный IP или домен сервера
- Порты (3478, 5349)
- Регион (страна/город)
- Секрет HMAC (для генерации credentials)

> API и инструкции по регистрации будут опубликованы отдельно.

---

## Мониторинг (опционально)

Если у тебя есть Prometheus + Grafana, добавь scrape job:

```yaml
# prometheus.yml
- job_name: 'coturn'
  static_configs:
    - targets: ['ВАШ_IP:9641']
      labels:
        server: 'coturn'
        location: 'твой-город'
  metrics_path: '/metrics'
  scrape_interval: 15s
```

Доступные метрики:

| Метрика | Описание |
|---|---|
| `turn_total_allocations` | Активные TURN сессии |
| `turn_total_traffic_sentb` | Отправлено байт (всего) |
| `turn_total_traffic_rcvb` | Получено байт (всего) |
| `turn_traffic_sentb{user}` | Трафик по пользователям |
| `stun_binding_request` | STUN запросы |
| `process_open_fds` | Открытые файловые дескрипторы |

---

## Устранение проблем

**TLS не поднимается:**
```bash
# Проверь права на archive директорию
ls -la /etc/letsencrypt/archive/
# Должно быть 755, не 700
chmod 755 /etc/letsencrypt/archive/
```

**Relay кандидат не появляется в ICE:**
```bash
# Проверь что relay диапазон открыт
iptables -L INPUT -n | grep 49152
# Проверь логи котурна
docker compose -f /opt/coturn/docker-compose.yml logs | grep "relay addr"
```

**Ошибка "external IP more than once":**
```bash
# Убери дублирующиеся директивы из конфига
# Оставь только external-ip, убери relay-ip если есть
grep -n "ip" /opt/coturn/config/turnserver.conf
```

**Высокие потери пакетов в UDP тесте:**

Это нормально для `turnutils_uclient -y` (loopback тест). Проверяй через WebRTC tester в браузере или тест с двух разных машин.

---

## Структура файлов

```
/opt/coturn/
├── docker-compose.yml
├── config/
│   └── turnserver.conf
└── certs/
    ├── fullchain.pem
    └── privkey.pem
```

---

*Мануал подготовлен для проекта MirBeer VPN / кастомный клиент Telegram.*
*Версия: 1.0 | Апрель 2026*
