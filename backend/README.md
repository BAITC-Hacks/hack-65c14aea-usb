# Backend

Backend проекта на Python 3.12+, FastAPI, PostgreSQL 16, Elasticsearch 8.x, Redis 7 и локальных multilingual embeddings через FastEmbed/ONNX.

## Ответственность

- импорт и валидация CSV-датасета;
- хранение нормализованного каталога в PostgreSQL;
- поиск по городу и категории;
- исключение занятых на выбранную дату кандидатов;
- фильтрация по бюджету, формату, языку и длительности;
- гибридный семантический поиск embeddings + BM25;
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
4. FastEmbed строит 384-мерный вектор запроса локальной multilingual MiniLM-моделью.
5. Elasticsearch объединяет точный cosine similarity (70%) и BM25 (30%) внутри города и категории.
6. Кандидаты получают бизнес-балл по бюджету, формату, языку, длительности и релевантности описания.
7. При равном балле применяется стабильная сортировка по `id`.
8. Объяснение строится из подтверждённых условий и наиболее близкого по смыслу предложения профиля.

LLM может переформулировать проверенные факты, но не выбирает кандидатов и не придумывает причины. Без внешнего AI API используется детерминированный шаблонный fallback.

## Хранилища

- **PostgreSQL** — источник истины для каталога и значений формы.
- **Elasticsearch** — индекс кандидатов, BM25 и точный cosine score по `dense_vector`.
- **Redis** — кэш полного ответа рекомендации по каноническому ключу запроса; TTL по умолчанию 300 секунд. На подключение и операцию кэша отводится не более 250 мс, поэтому при недоступности Redis API продолжает работать без кэша.

Импортёр валидирует CSV через Pydantic, строит embeddings, синхронизирует PostgreSQL, полностью пересоздаёт индекс Elasticsearch и очищает устаревший кэш.

Embedding-модель `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` фиксирована в конфигурации. Веса скачиваются во время Docker build и не требуют внешнего API при запуске.

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
pip install -r requirements-dev.txt
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
