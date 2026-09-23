from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.dataset import load_dataset
from app.llm import qa


class FakeClient:
    def __init__(self, text=None, raise_exc=None): self._text, self._raise = text, raise_exc
    class _Chat:
        def __init__(self, outer): self._outer = outer
        class _Comp:
            def __init__(self, outer): self._outer = outer
            def create(self, **_):
                if self._outer._raise: raise self._outer._raise
                return type("R", (), {"choices": [type("C", (), {"message": type("M", (), {"content": self._outer._text})})]})
        @property
        def completions(self): return FakeClient._Chat._Comp(self._outer)
    @property
    def chat(self): return FakeClient._Chat(self)


@pytest.fixture()
def ds():
    return load_dataset(Path(__file__).resolve().parents[2].parent / "data")


def test_llm_answer_is_used(monkeypatch, ds):
    monkeypatch.setattr(qa, "get_client", lambda: FakeClient(text="You are close to Senior."))
    out = qa.answer_question(ds, "E0028", "How close am I?", "en")
    assert out["generated_by"] == "llm" and out["answer"] == "You are close to Senior."


def test_no_client_falls_back_to_template(monkeypatch, ds):
    monkeypatch.setattr(qa, "get_client", lambda: None)
    out = qa.answer_question(ds, "E0028", "Why this step?", "en")
    assert out["generated_by"] == "rules" and out["answer"]


def test_llm_error_falls_back(monkeypatch, ds):
    monkeypatch.setattr(qa, "get_client", lambda: FakeClient(raise_exc=RuntimeError("boom")))
    out = qa.answer_question(ds, "E0028", "Why this step?", "en")
    assert out["generated_by"] == "rules" and out["answer"]
