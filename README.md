# Smart Contractor Match — #79-lite

Объяснимый подбор event-подрядчиков в Казахстане. Пользователь задаёт город, дату, формат, категорию и бюджет, а сервис возвращает до трёх свободных подрядчиков с проверяемыми персональными объяснениями.

## Что реализовано

- три явных исхода: подборка, категории нет в городе, кандидаты есть, но не проходят условия;
- жёсткое исключение занятых, слишком дорогих и несовместимых профилей;
- локальные multilingual embeddings для русского текста без внешнего AI API;
- гибридный поиск: 70% cosine similarity по embeddings и 30% BM25;
- детерминированное бизнес-ранжирование и стабильный tie-break по `id`;
- персональные объяснения с конкретным фрагментом профиля;
- интерактивная карта, где выбор города сразу повторяет запрос к backend;
- три готовых демо-сценария Definition of Done прямо в интерфейсе;
- PostgreSQL как источник каталога, Elasticsearch для поиска, Redis для кэша;
- явная маркировка 13 синтетических профилей.

## Архитектура

```text
CSV (66 профилей)
        │
        ▼
Docker importer ──► PostgreSQL
        │
        ├──► multilingual MiniLM embeddings (384)
        │
        └──► Elasticsearch: keyword + BM25 + dense_vector
                                      │
Vue 3 ──► FastAPI ──► Redis cache ────┤
                                      ▼
                         фильтры → score → объяснения
```

Модель `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` запускается локально через FastEmbed/ONNX. При импорте создаётся вектор каждого профиля. Для запроса вычисляется вектор тех же размеров, после чего Elasticsearch считает точный cosine score только внутри уже отфильтрованных города и категории. При 66 профилях точный поиск быстрее и детерминированнее approximate kNN.

LLM не принимает бизнес-решения и не придумывает факты: карточка строится только из календаря, цены, структурированных условий и наиболее близкого по смыслу предложения исходного описания.

## Запуск

Требуются Docker Compose и Node.js.

### 1. Backend и хранилища

```bash
cd backend
cp .env.example .env
docker compose up -d --build
```

Первый build скачивает multilingual embedding-модель размером около 220 МБ и сохраняет её внутри Docker image. Во время последующих запусков и демонстрации внешний AI API не нужен.

Проверка:

```bash
curl http://localhost:8000/ready
```

### 2. Frontend

В другом терминале:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

- интерфейс: http://localhost:5173
- Swagger: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Elasticsearch: localhost:9200

Если порт занят, его можно переопределить в `backend/.env`.

## Три демо-запроса

Все команды выполняются после запуска backend.

### 1. Плотная категория: фотографы

Показывает реальное ранжирование нескольких доступных профилей.

```bash
curl -sS http://localhost:8000/api/v1/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"city":"Алматы","event_date":"2026-10-10","event_format":"свадьба","category":"Фотограф","budget_kzt":6000000}' \
  | python -m json.tool
```

### 2. Редкая категория: флористы

Возвращает меньше трёх карточек и словами объясняет нехватку.

```bash
curl -sS http://localhost:8000/api/v1/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"city":"Алматы","event_date":"2026-10-10","event_format":"свадьба","category":"Флорист","budget_kzt":6000000}' \
  | python -m json.tool
```

### 3. Кандидаты есть, но никто не проходит

Бюджет намеренно ниже минимальной цены. Интерфейс показывает причины вместо пустого экрана.

```bash
curl -sS http://localhost:8000/api/v1/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"city":"Алматы","event_date":"2026-10-10","event_format":"свадьба","category":"Фотограф","budget_kzt":1}' \
  | python -m json.tool
```

Для демонстрации влияния календаря повторите первый запрос с датой `2026-11-14`: состав тройки и дата в объяснениях изменятся.

## Проверки

```bash
cd backend && pytest
cd frontend && npm test
cd frontend && npm run build
```

Backend также проверяет занятость, детерминизм, различие дат, все бизнес-исходы, персональность объяснений и реальные 66 строк датасета.

Подробности: [backend](backend/README.md) и [frontend](frontend/README.md).
