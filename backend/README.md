# Backend

Backend проекта на Python 3.12+, FastAPI, Pydantic v2 и Elasticsearch 8.x.

## Ответственность

- импорт и валидация JSONL-датасета;
- поиск по городу и категории;
- исключение занятых на выбранную дату кандидатов;
- фильтрация по бюджету, формату, языку и длительности;
- детерминированное ранжирование;
- возврат до трёх карточек с индивидуальными объяснениями;
- явное различение трёх исходов из ТЗ.

Бронирование, заявки и уведомления не входят в проект.

## Структура

```text
backend/
├── app/
│   ├── api/             # FastAPI-маршруты
│   ├── core/            # конфигурация и логирование
│   ├── models/          # доменные модели
│   ├── repositories/    # запросы к Elasticsearch
│   ├── schemas/         # Pydantic-схемы
│   └── services/        # фильтрация, скоринг, объяснения
├── data/                # исходный JSONL
├── scripts/             # индекс и импорт данных
└── tests/               # unit- и integration-тесты
```

## Основной API

### `POST /api/v1/recommendations`

```json
{
  "city": "Алматы",
  "event_date": "2026-11-14",
  "event_format": "свадьба",
  "category": "Фотограф",
  "budget_kzt": 300000,
  "duration_hours": 6,
  "language": "казахский"
}
```

`duration_hours` и `language` опциональны, остальные поля обязательны.

В ответе возвращаются `status`, массив `items` длиной от 0 до 3 и понятное `message`. Карточка содержит `id`, имя, категории, город, цену, признак `synthetic` и персональное `explanation`.

| Статус | Значение |
|---|---|
| `matched` | Найден хотя бы один подходящий подрядчик. |
| `category_not_found` | В городе нет профилей выбранной категории. |
| `no_eligible_candidates` | Профили есть, но все заняты или не проходят условия. |

Дополнительные маршруты:

- `GET /health` — процесс API работает;
- `GET /ready` — Elasticsearch и индекс доступны;
- `GET /api/v1/catalog/options` — значения для полей формы.

## Пайплайн рекомендации

1. Pydantic нормализует и валидирует запрос.
2. Отдельный запрос проверяет наличие категории в городе.
3. Жёсткие фильтры исключают занятую дату и несовместимые условия.
4. Кандидаты получают составной балл по бюджету, формату, языку, длительности и BM25-релевантности описания с русской морфологией Elasticsearch.
5. При равном балле применяется стабильная сортировка по `id`.
6. Объяснение строится только из подтверждённых данных конкретного кандидата.

LLM может переформулировать проверенные факты, но не выбирает кандидатов и не придумывает причины. Без внешнего AI API используется детерминированный шаблонный fallback.

## Elasticsearch

- `id`, `city`, `categories`, `event_formats`, `languages`, `busy_dates` — `keyword`;
- `price_from_kzt` — `long`;
- `max_hours` — `float`, допускается `null`;
- `description` — `text` с русскоязычным анализатором;
- `synthetic`, `city_imputed`, `price_imputed` — `boolean`.

Синтетические записи обязательно имеют `synthetic: true`, и признак передаётся клиенту.

## Локальный запуск

### Весь backend через Docker Compose

```bash
cd backend
cp .env.example .env
docker compose up -d --build
docker compose run --rm api \
  python -m scripts.index_dataset data/sample-contractors.jsonl --recreate
```

После получения основного файла замените последнюю команду на:

```bash
docker compose run --rm api python -m scripts.index_dataset --recreate
```

API: `http://localhost:8000`, Swagger UI: `http://localhost:8000/docs`.
Если порт занят, задайте, например, `API_PORT=8100` в `.env`.

### FastAPI локально, Elasticsearch через Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.index_dataset
uvicorn app.main:app --reload --port 8000
```

Перед импортом запустите Elasticsearch и подготовьте окружение:

```bash
cp .env.example .env
docker compose up -d elasticsearch
python -m scripts.index_dataset --recreate
```

Если основной датасет ещё не получен, для smoke-теста используйте:

```bash
python -m scripts.index_dataset data/sample-contractors.jsonl --recreate
```

Проверка тестов: `pytest`.

## Обязательные проверки

- занятый подрядчик не попадает в ответ;
- одинаковый запрос даёт одинаковый порядок;
- другая дата может изменить выдачу;
- корректно различаются все три статуса;
- `max_hours: null` корректно работает для услуг без присутствия;
- объяснение содержит только факты выбранного профиля;
- при 1–2 результатах объясняется, почему карточек меньше трёх;
- синтетический профиль явно помечается.
