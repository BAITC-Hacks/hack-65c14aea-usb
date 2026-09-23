# Backend

Backend проекта на Python 3.12+, FastAPI, PostgreSQL 16, Elasticsearch 8.x и Redis 7.

## Ответственность

- импорт и валидация CSV-датасета;
- хранение нормализованного каталога в PostgreSQL;
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
│   ├── database/        # SQLAlchemy-модели PostgreSQL
│   ├── models/          # доменные модели
│   ├── repositories/    # PostgreSQL + Elasticsearch
│   ├── schemas/         # Pydantic-схемы
│   └── services/        # фильтрация, скоринг, объяснения и кэш
├── data/                # исходный CSV
├── scripts/             # синхронизация PostgreSQL и Elasticsearch
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
- `GET /ready` — PostgreSQL, Elasticsearch и Redis доступны;
- `GET /api/v1/catalog/options` — значения для полей формы.

## Пайплайн рекомендации

1. Pydantic нормализует и валидирует запрос.
2. Отдельный запрос проверяет наличие категории в городе.
3. Жёсткие фильтры исключают занятую дату и несовместимые условия.
4. Кандидаты получают составной балл по бюджету, формату, языку, длительности и BM25-релевантности описания с русской морфологией Elasticsearch.
5. При равном балле применяется стабильная сортировка по `id`.
6. Объяснение строится только из подтверждённых данных конкретного кандидата.

LLM может переформулировать проверенные факты, но не выбирает кандидатов и не придумывает причины. Без внешнего AI API используется детерминированный шаблонный fallback.

## Хранилища

- **PostgreSQL** — источник истины для каталога и значений формы.
- **Elasticsearch** — индекс кандидатов, фильтрация и BM25-поиск.
- **Redis** — кэш полного ответа рекомендации по каноническому ключу запроса; TTL по умолчанию 300 секунд. При недоступности Redis API продолжает работать без кэша.

Импортёр валидирует CSV через Pydantic, одним запуском синхронизирует PostgreSQL, полностью пересоздаёт индекс Elasticsearch и очищает устаревший кэш.

### Elasticsearch

- `id`, `city`, `categories`, `event_formats`, `languages`, `busy_dates` — `keyword`;
- `price_from_kzt` — `long`;
- `max_hours` — `float`, допускается `null`;
- `description` — `text` с русскоязычным анализатором;
- `synthetic`, `city_imputed`, `price_imputed` — `boolean`.

Синтетические записи обязательно имеют `synthetic: true`, и признак передаётся клиенту.

## Локальный запуск

### Весь backend одной командой

```bash
cd backend
cp .env.example .env
docker compose up -d --build
```

Цепочка запуска в Compose:

1. PostgreSQL, Redis и Elasticsearch проходят healthcheck.
2. Одноразовый `importer` создаёт таблицу и загружает `data/hackathon-dataset-anonymized.csv` в PostgreSQL и Elasticsearch.
3. API стартует только после успешного завершения импортёра.

API: `http://localhost:8000`, Swagger UI: `http://localhost:8000/docs`.
PostgreSQL, Redis и Elasticsearch снаружи доступны на портах `5432`, `6379` и `9200`.

Если стандартные порты заняты, задайте свободные только для хоста:

```bash
API_PORT=8100 POSTGRES_PORT=5433 REDIS_PORT=6380 docker compose up -d --build
```

Повторная синхронизация CSV:

```bash
docker compose run --rm importer
```

Проверка состояния и логов:

```bash
docker compose ps -a
docker compose logs importer api
```

Остановка без удаления данных:

```bash
docker compose down
```

### Запуск тестов локально

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Обязательные проверки

- занятый подрядчик не попадает в ответ;
- одинаковый запрос даёт одинаковый порядок;
- другая дата может изменить выдачу;
- корректно различаются все три статуса;
- `max_hours: null` корректно работает для услуг без присутствия;
- объяснение содержит только факты выбранного профиля;
- при 1–2 результатах объясняется, почему карточек меньше трёх;
- синтетический профиль явно помечается.
