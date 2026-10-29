# Отчёт по ЛР 1
Траектория: AI и MLOps

## Этап А

### Требования
| Требование | Как реализовано |
|------------|-----------------|
| Пакет в src-layout, устанавливается в чистое окружение | `pyproject.toml`, `src/school/` |
| Модель `Submission` (неизменяемая) | `src/school/domain/models.py` |
| Разбор JSON, валидация обязательных полей, часового пояса, AI-декларации | `src/school/validation/validator.py` (через pydantic) |
| Ошибка содержит `code`, `field`, `message`; вход не мутируется | `src/school/domain/errors.py` |
| Различаются ошибка формата, нарушение схемы, конфликт id | `format_error` / `schema_error` / `id_conflict` |
| Тот же id + тот же хеш → уже принятая сдача; другой хеш → conflict | `src/school/repository/memory.py: InMemorySubmissionRepository.accept` |
| In-memory репозиторий за интерфейсом | `src/school/domain/contracts.py : SubmissionRepository` |
| Публичные функции аннотированы; домен не читает stdin и не ходит в HTTP | весь `domain/`; файлы читают только `sources/`|
| AI: импорт корпуса + manifest с id, хешами и версией обработки | `src/school/services/ingestion.py`, `build_manifest` |
| AI: исходные text/code отделены от будущих признаков | `Submission` хранит только сырой контент; `BasicFeatureExtractor` создает признаки |
| AI: `ai_declaration` не используется как метка | явно исключено из `BasicFeatureExtractor.extract` |
| AI: конфигурация режима ML/LLM, оба дают детерминированный baseline | `src/school/ai/config.py`, `src/school/ai/stub_model.py` |

### Приёмка этапа А
| Сценарий | Тест |
|----------|------|
| Корректная запись принимается | `test_validation.py::test_valid_submission` |
| Неверный timestamp | `test_validation.py::test_missing_timezone_is_schema_error` |
| Пустой `student_id` | `test_validation.py::test_empty_student_id_is_schema_error` |
| Неизвестное поле | `test_validation.py::test_unknown_field_is_schema_error` |
| Неверные типы | `test_validation.py::test_bool_schema_version_rejected` |
| Дубликат не увеличивает число сдач | `test_repository.py::test_duplicate_same_hash` |
| Конфликт не перезаписывает запись | `test_repository.py::test_conflict_same_id_different_content` |
| Повреждённая JSON-строка не останавливает импорт | `test_ingestion.py::test_ingestion_handles_broken_json` |
| Установка в чистое окружение | Ручная проверка через `pip install -e .` в новом venv |

### Проверка:

```bash
    pip install -e .
    pytest -q
```

### Где выполняется валидация:
Валидация выполняется в `src/school/validation/validator.py` (parse_submission). Её вызывает `IngestionService.ingest`. Аннотации типов не проверяются интерпретатором во время выполнения. JSON из файла может содержать "schema_version": true или "student_id": 42, и без явной проверки (которую обеспечивает Pydantic с strict=True) такой объект попал бы в доменную модель, нарушив инварианты.

## Этап Б

### Требования

| Требование | Как реализовано |
|------------|-----------------|
| Контракт `Analyzer.analyze(submission, context) -> AnalysisReport` (синхронный) | `src/school/domain/contracts.py` |
| Context передаёт требования Assignment и доступ к данным через интерфейс | `AnalysisContext (assignment, template_text, config_hash)` |
| В отчёте `analyzer_id`, `analyzer_version` | `src/school/domain/models.py` |
| `LengthAnalyzer`: непустые строки текста и кода, пояснение в `rubric_feedback`, `score=null` | `src/school/analyzers/length.py` |
| `TemplateAnalyzer`: точные строки шаблона → `similarity` + пояснение | `src/school/analyzers/template.py` |
| Номера строк evidence относятся к исходному содержимому | Сквозная нумерация |
| JSONL-источник и in-memory источник | `src/school/sources/jsonl_source.py, memory_source.py` |
| Один набор контрактных тестов на оба источника и на все анализаторы | `tests/test_analyzers.py`, `tests/test_sources.py` |
| Центральный сервис выбирает анализатор по реестру, без ветвления по классам | `src/school/analyzers/registry.py`, `src/school/services/analysis.py`|
| AI: интерфейсы подготовки входа и формирования feedback | `src/school/ai/feature_extractor.py`, `feedback_builder.py` |
| AI: stub модели с тем же контрактом результата | `src/school/ai/stub_model.py` |
| AI: `config_hash` зафиксирован | `src/school/ai/config.py` (`ModeConfig.config_hash`) |
| AI: LLM — версия шаблона запроса, ML — версия схемы признаков | Поля template_version / feature_schema_version в ModeConfig |

### Проверки:

| Проверка | Тест |
|----------|------|
| Валидный импорт | `test_ingestion.py::test_ingestion_accepts_valid` |
| Повреждённый JSON | `test_ingestion.py::test_ingestion_handles_broken_json` |
| Неверные типы | `test_validation.py::test_bool_schema_version_rejected` |
| Дубликат | `test_repository.py::test_duplicate_same_hash` |
| Конфликт | `test_repository.py::test_conflict_same_id_different_content` |
| Ошибка анализатора | `test_analysis.py::test_analysis_error_propagates` |
| Освобождение ресурса | `test_sources.py::test_jsonl_source_releases_resource` |
| Диапазоны evidence | `test_analyzers.py::test_template_evidence_within_source_bounds` |
| Неизменность исходного объекта | `test_analyzers.py::test_submission_object_is_immutable` |

### Примененные решения:
1. Разделение валидации и доменной модели: разделены доменные и pydantic модели, т.к. нужно сохранить оригинальные строки без изменений, чтобы хеш был стабильным, а номера строк соответствовали исходному файлу. Доменные модели неизменяемые.

2. Отказоустойчивый импорт: одна ошибка не ломает весь процесс импорта.

3. Расширяемость через реестр и протоколы: AnalysisService не знает ничего о конкретных классах анализаторов. Поэтому для нового анализатора достаточно создать класс, реализующий протокол анализатора и зарегистрировать.

4. Явный контекст анализаторов: Анализаторы не обращаются к глобальным переменным или репозиториям, чтобы узнать правила задания. Метод analyze принимает только два аргумента: Submission и AnalysisContext.

### Измерения

Время и память по требованиям ЛР 1 не измеряются. Полный набор тестов выполняется примерно за 0.1–0.2 с. Анализ небольшого датасета занимает доли секунды из-за in-memory структуры.