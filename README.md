## Установка
Требуется Python ≥ 3.10. Все зависимости объявлены в `pyproject.toml`.

**venv:**
```bash
git clone https://github.com/GGiovanni9152/PythonLabs.git
cd PythonLabs
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Анализаторы
| id | Что делает |
|----|------|
| length | Число непустых строк текста и кода; пояснение в rubric_feedback, score=null|
| emplate | Точные строки разрешённого шаблона в тексте/коде similarity + evidence (сквозная нумерация строк). Совпадение с шаблоном явно разрешено|
| model_stub | Заглушка AI-ветки: FeatureExtractor → StubModel → FeedbackBuilder. Возвращает детерминированный базовый результат с фиксированным config_hash|

## Проверка
```bash
pytest -q
```
## Структура

```text
src/school/
  domain/                   #понятия и контракты
    models.py               # Submission, AIDeclaration, Assignment, AnalysisReport
    errors.py               # SubmissionError с code, field, message
    contracts.py            # Protocol: Analyzer, SubmissionSource, SubmissionRepository, Model
  validation/               # Проверка внешних данных
    pydantic_models.py      # Схемы валидации
    validator.py            # parse_submission: JSON → pydantic → domain model
  repository/               # Хранение
    memory.py               # InMemorySubmissionRepository
  sources/                  # Адаптеры чтения
    jsonl_source.py         # Построчное чтение
    memory_source.py        # InMemorySource
  analyzers/                # Реализации analyzers
    length.py               
    template.py
    registry.py             # AnalyzerRegistry
  ai/                       # Ветка MLOps
    config.py               # ModeConfig (ml/llm, versions, config_hash)
    feature_extractor.py    # Извлечение признаков
    stub_model.py           # Детерминированная заглушка модели
  services/                 # Координация
    ingestion.py            # IngestionService, load_assignments, build_manifest
    analysis.py             # сборка контекста и запуск анализатора из реестра
```

Зависимости направлены строго к domain.