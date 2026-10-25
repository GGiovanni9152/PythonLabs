from school.sources.jsonl_source import JSONLSource
from school.sources.memory_source import InMemorySource


def test_memory_source_iter(tmp_path):
    src = InMemorySource(["{}", "[]"])
    assert list(src.iter_raw()) == ["{}", "[]"]


def test_jsonl_source_reads_lines(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"a":1}\n\n{"b":2}\n', encoding="utf-8")
    src = JSONLSource(p)

    assert list(src.iter_raw()) == ['{"a":1}', '{"b":2}']


def test_jsonl_source_releases_resource(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"a":1}\n', encoding="utf-8")
    src = JSONLSource(p)
    consumed = list(src.iter_raw())

    assert consumed == ['{"a":1}']

    p.write_text('{"a":2}\n', encoding="utf-8")
    assert list(JSONLSource(p).iter_raw()) == ['{"a":2}']