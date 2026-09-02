import open_webui.models.simon_lex_index as simon_lex_index
from open_webui.models.simon_lex_index import _build_subqueries, flatten_content


def test_build_subqueries_dedupes_and_respects_max_branches():
    subqueries = _build_subqueries(["alpha", "beta", "gamma", "delta"], max_branches=4)

    assert len(subqueries) <= 4
    assert len(set(subqueries)) == len(subqueries)


def test_flatten_content_handles_string_list_and_dict():
    assert flatten_content(" hello  world ") == "hello world"
    assert flatten_content({"text": "  hi there  "}) == "hi there"
    assert (
        flatten_content(
            [{"type": "text", "text": "hello"}, {"type": "text", "text": "world"}]
        )
        == "hello world"
    )


def test_ensure_schema_runs_ddl_only_once_per_process(monkeypatch):
    class DbStub:
        def __init__(self):
            self.statements = []
            self.commits = 0

        def execute(self, statement):
            self.statements.append(str(statement))

        def commit(self):
            self.commits += 1

    db = DbStub()
    monkeypatch.setattr(simon_lex_index, "_SCHEMA_READY", False)
    monkeypatch.setattr(simon_lex_index, "is_supported_database", lambda: True)

    simon_lex_index.ensure_schema(db)
    simon_lex_index.ensure_schema(db)

    assert len(db.statements) == 5
    assert db.commits == 1
