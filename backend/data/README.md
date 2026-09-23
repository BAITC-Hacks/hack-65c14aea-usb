# Данные

Основной файл организаторов уже размещён здесь:

`hackathon-dataset-anonymized.csv`

В нём 66 уникальных профилей, из них 13 помечены `synthetic=true`. Контрольная сумма SHA-256:

`6a724b6b7dfb5973343e68ba18dadb60fc807d87e3d78f03ee86fb26cb089f7d`

При `docker compose up` сервис `importer` автоматически:

1. проверяет структуру и значения CSV через Pydantic;
2. синхронизирует таблицу `contractors` в PostgreSQL;
3. пересоздаёт индекс Elasticsearch;
4. очищает Redis-кэш рекомендаций.

Ручной повторный импорт:

```bash
docker compose run --rm importer
```

Файл `sample-contractors.jsonl` оставлен только для изолированных unit-тестов старого индексатора и не используется Docker-цепочкой.
