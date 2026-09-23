# Данные

Для боевого запуска положите выданный организаторами файл сюда под именем:

`hackathon-dataset-anonymized.jsonl`

Файл `sample-contractors.jsonl` содержит только шесть демонстрационных профилей. Все они намеренно помечены `synthetic: true` и не заменяют основной датасет из 66 записей.

Импорт основного набора:

```bash
python -m scripts.index_dataset --recreate
```

Импорт демонстрационного набора:

```bash
python -m scripts.index_dataset data/sample-contractors.jsonl --recreate
```

