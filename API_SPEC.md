# Qwen Image Generation API — Техническое задание

## Обзор

REST API для генерации изображений на базе модели **Qwen-Image (int8 квантизация)**, развёрнутой на VPS с GPU NVIDIA A100 40GB.

API доступно публично по адресу: `https://qwen.rossiinfrastructure.ru`

---

## Инфраструктура

- **Сервер:** VPS, Ubuntu 24.04, NVIDIA A100-PCIE-40GB
- **Модель:** `dimitribarbot/Qwen-Image-int8wo` (~20GB VRAM)
- **Веб-сервер:** nginx (настроен, SSL через Let's Encrypt)
- **API сервер:** FastAPI + uvicorn, порт 8088 (проксируется через nginx)
- **Публичный URL:** `https://qwen.rossiinfrastructure.ru` — доступен с любой машины

---

## Аутентификация

Все запросы (кроме `/health`) требуют Bearer-токен в заголовке:

```
Authorization: Bearer <API_TOKEN>
```

Без токена или с неверным токеном возвращается `401 Unauthorized`.

---

## Эндпоинты

### GET /health

Проверка доступности сервиса. Авторизация не требуется.

**Ответ:**
```json
{"status": "ok"}
```

---

### POST /generate

Генерация изображения по текстовому описанию.

**Headers:**
```
Authorization: Bearer <API_TOKEN>
Content-Type: multipart/form-data
```

**Параметры (form-data):**

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|---|---|---|---|---|
| `prompt` | string | ✅ | — | Текстовое описание изображения |
| `width` | integer | ❌ | 1024 | Ширина в пикселях |
| `height` | integer | ❌ | 1024 | Высота в пикселях |
| `steps` | integer | ❌ | 4 | Количество шагов генерации |
| `guidance_scale` | float | ❌ | 0.0 | Сила следования промпту |

**Ответ:** PNG изображение (`image/png`)

**Пример запроса:**
```bash
curl -X POST https://qwen.rossiinfrastructure.ru/generate \
  -H "Authorization: Bearer <API_TOKEN>" \
  -F "prompt=a cat in space, 4K" \
  -o result.png
```

**Пример на JavaScript:**
```js
const form = new FormData();
form.append("prompt", "a cat in space, 4K");

const res = await fetch("https://qwen.rossiinfrastructure.ru/generate", {
  method: "POST",
  headers: { "Authorization": "Bearer <API_TOKEN>" },
  body: form,
});

const blob = await res.blob();
```

---

## Коды ответов

| Код | Описание |
|---|---|
| 200 | Успех, тело ответа — PNG изображение |
| 401 | Неверный или отсутствующий токен |
| 500 | Ошибка генерации (детали в теле ответа) |

---

## Примечания

- Первый запрос после старта сервера занимает **1-3 минуты** — модель загружается в VRAM
- Последующие запросы выполняются за **3-10 секунд**
- При одновременном использовании LM Studio на том же сервере — его необходимо остановить перед запуском генерации (нехватка VRAM)
- Модель поддерживает промпты на **английском и китайском** языках
- Максимальный размер запроса: **20MB** (ограничение nginx)
