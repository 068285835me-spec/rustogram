# Rustogram

**🇷🇺 Русский** | [🇬🇧 English](#english)

---

## 🇷🇺 Русский

### Что такое Rustogram?

Rustogram — форк официального клиента [Telegram Desktop](https://github.com/telegramdesktop/tdesktop), разработанный для обхода DPI-блокировок голосовых и видеозвонков.

Если вы находитесь в регионе где Telegram заблокирован или деградирован — Rustogram позволяет звонить без помех, используя собственную сеть TURN-релеев.

### Как это работает?

Telegram использует протокол WebRTC для голосовых и видеозвонков. При установке соединения WebRTC собирает список ICE-кандидатов — адресов через которые могут идти медиапотоки.

Rustogram добавляет в этот список **собственные TURN-серверы** с высоким приоритетом. Если официальные серверы Telegram заблокированы — соединение устанавливается через наши серверы. Весь медиатрафик остаётся **зашифрованным end-to-end** (SRTP/DTLS) — наши серверы видят только зашифрованные пакеты.

```
Вы ──→ TURN-сервер Rustogram ──→ Собеседник
           (зашифровано E2E)
```

### Скачать

Готовые сборки доступны в разделе [Releases](../../releases):

| Платформа | Файл |
|-----------|------|
| Linux x64 | `rustogram-linux-x64.zip` |
| Windows (скоро) | — |
| Android (скоро) | — |

### Собрать самому

Если вы хотите убедиться что сборка соответствует исходному коду:

```bash
# 1. Клонируем репозиторий
git clone https://github.com/068285835me-spec/rustogram.git
cd rustogram

# 2. Смотрим наши изменения
cat mirbeer-turn.patch      # изменения в исходниках Telegram
cat mirbeer_turn.cpp        # наш модуль (HTTP клиент + кэш TURN серверов)
cat mirbeer_turn.h          # заголовочный файл

# 3. Клонируем оригинальный Telegram Desktop
#    (версия берётся из файла .upstream-tag — она синхронизируется с
#    последним релизом tdesktop автоматически)
git clone --depth=1 --recursive \
  --branch "$(cat .upstream-tag)" \
  https://github.com/telegramdesktop/tdesktop.git

# 4. Применяем патч
cd tdesktop
python3 ../apply_mirbeer.py
cp ../mirbeer_turn.cpp Telegram/SourceFiles/calls/
cp ../mirbeer_turn.h Telegram/SourceFiles/calls/

# 5. Собираем (требует Docker)
# Подробные инструкции: https://github.com/telegramdesktop/tdesktop/blob/dev/docs/building-linux.md
```

Или используйте GitHub Actions — каждый push в ветку `dev` автоматически собирает бинарник.

### Наши изменения

Мы изменили **3 файла** в оригинальном коде Telegram Desktop:

| Файл | Изменение |
|------|-----------|
| `Telegram/CMakeLists.txt` | Добавлены наши файлы в сборку |
| `Telegram/SourceFiles/core/application.cpp` | Инициализация TURN провайдера при старте |
| `Telegram/SourceFiles/calls/calls_call.cpp` | Инжект наших TURN серверов в ICE конфигурацию |

И добавили **2 новых файла**:
- `mirbeer_turn.h` — интерфейс модуля
- `mirbeer_turn.cpp` — HTTP клиент, парсинг JSON, 24-часовой кэш

### Поднять свой TURN-сервер

Хотите помочь проекту и поднять собственный TURN-сервер? Смотрите мануал:

👉 [coturn-deploy-manual.md](coturn-deploy-manual.md) — пошаговая инструкция по развёртыванию
👉 [turn-network-registration.md](turn-network-registration.md) — как зарегистрировать сервер в сети

После развёртывания вы можете зарегистрировать сервер в нашей сети — тогда все пользователи Rustogram смогут им пользоваться.

### Безопасность

- Rustogram не собирает и не передаёт никаких данных о пользователях
- Наши TURN-серверы видят только зашифрованный трафик — содержимое разговоров недоступно
- Исходный код открыт — вы можете проверить каждую строку изменений
- HMAC-авторизация на TURN-серверах — открытый relay невозможен

### Лицензия

Rustogram распространяется под лицензией [GNU GPL v3](LICENSE), как и оригинальный Telegram Desktop.

---

## <a name="english"></a>🇬🇧 English

### What is Rustogram?

Rustogram is a fork of the official [Telegram Desktop](https://github.com/telegramdesktop/tdesktop) client, designed to bypass DPI-based blocking of voice and video calls.

If you are in a region where Telegram is blocked or degraded — Rustogram lets you call without interruptions using our own network of TURN relay servers.

### How does it work?

Telegram uses the WebRTC protocol for voice and video calls. During connection setup, WebRTC collects a list of ICE candidates — addresses through which media streams can flow.

Rustogram adds **our own TURN servers** to this list with high priority. If Telegram's official servers are blocked — the connection is established through our servers. All media traffic remains **end-to-end encrypted** (SRTP/DTLS) — our servers only see encrypted packets.

```
You ──→ Rustogram TURN server ──→ Your contact
              (E2E encrypted)
```

### Download

Ready-to-use builds are available in the [Releases](../../releases) section:

| Platform | File |
|----------|------|
| Linux x64 | `rustogram-linux-x64.zip` |
| Windows (coming soon) | — |
| Android (coming soon) | — |

### Build it yourself

If you want to verify that the build matches the source code:

```bash
# 1. Clone the repository
git clone https://github.com/068285835me-spec/rustogram.git
cd rustogram

# 2. Review our changes
cat mirbeer-turn.patch      # changes to Telegram source files
cat mirbeer_turn.cpp        # our module (HTTP client + TURN server cache)
cat mirbeer_turn.h          # header file

# 3. Clone original Telegram Desktop
#    (the version is read from the .upstream-tag file — it is kept
#    in sync with the latest tdesktop release automatically)
git clone --depth=1 --recursive \
  --branch "$(cat .upstream-tag)" \
  https://github.com/telegramdesktop/tdesktop.git

# 4. Apply the patch
cd tdesktop
python3 ../apply_mirbeer.py
cp ../mirbeer_turn.cpp Telegram/SourceFiles/calls/
cp ../mirbeer_turn.h Telegram/SourceFiles/calls/

# 5. Build (requires Docker)
# Detailed instructions: https://github.com/telegramdesktop/tdesktop/blob/dev/docs/building-linux.md
```

Or use GitHub Actions — every push to the `dev` branch automatically builds a binary.

### Our changes

We modified **3 files** in the original Telegram Desktop code:

| File | Change |
|------|--------|
| `Telegram/CMakeLists.txt` | Added our files to the build |
| `Telegram/SourceFiles/core/application.cpp` | Initialize TURN provider on app start |
| `Telegram/SourceFiles/calls/calls_call.cpp` | Inject our TURN servers into ICE configuration |

And added **2 new files**:
- `mirbeer_turn.h` — module interface
- `mirbeer_turn.cpp` — HTTP client, JSON parsing, 24-hour cache

### Run your own TURN server

Want to help the project by running your own TURN server? See the manual:

👉 [coturn-deploy-manual.md](coturn-deploy-manual.md) — step-by-step deployment guide
👉 [turn-network-registration.md](turn-network-registration.md) — how to register your server in the network

After deployment you can register your server in our network — then all Rustogram users will be able to use it.

### Security

- Rustogram does not collect or transmit any user data
- Our TURN servers only see encrypted traffic — call content is inaccessible
- Source code is open — you can review every line of our changes
- HMAC authorization on TURN servers — open relay is impossible

### License

Rustogram is distributed under the [GNU GPL v3](LICENSE) license, just like the original Telegram Desktop.

---

*Rustogram is not affiliated with Telegram Messenger LLP. This is an independent open-source project.*
