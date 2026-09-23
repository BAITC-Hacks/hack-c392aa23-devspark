from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engine.dataset import load_dataset
from app.llm import decide


class FakeMessage:
    def __init__(self, content): self.message = type("M", (), {"content": content})


class FakeCompletions:
    def __init__(self, payloads): self._payloads = list(payloads); self.calls = 0
    def create(self, **_):
        payload = self._payloads[min(self.calls, len(self._payloads) - 1)]; self.calls += 1
        if isinstance(payload, Exception):
            raise payload
        return type("R", (), {"choices": [FakeMessage(json.dumps(payload))]})


class FakeClient:
    def __init__(self, payloads): self.chat = type("C", (), {"completions": FakeCompletions(payloads)})


@pytest.fixture()
def ds():
    return load_dataset(Path(__file__).resolve().parents[2].parent / "data")


@pytest.fixture(autouse=True)
def clear_cache():
    decide._CACHE.clear(); yield; decide._CACHE.clear()


def _install(monkeypatch, payloads):
    client = FakeClient(payloads)
    monkeypatch.setattr(decide, "get_client", lambda: client)
    return client


def _valid_pick(ds):
    from app.llm.prompt import build_context
    built = build_context(ds, "E0028", None)
    event_id = built["candidate_ids"][0]
    kinds = sorted(built["factor_kinds_by_event"][event_id])[:3]
    return event_id, {"picks": [{"event_id": event_id, "rationale": "You can grow here.", "factors_used": kinds}], "not_recommended": [], "summary": "ok"}


def test_valid_pick_is_used(monkeypatch, ds):
    event_id, payload = _valid_pick(ds)
    _install(monkeypatch, [payload])
    result = decide.ai_recommendation(ds, "E0028")
    assert result is not None and result.generated_by == "llm"
    assert result.recommendations[0].event_id == event_id
    assert result.recommendations[0].rationale == "You can grow here."


def test_unknown_event_id_falls_back(monkeypatch, ds):
    bad = {"picks": [{"event_id": "EV_NOPE", "rationale": "x", "factors_used": ["target_gap", "availability", "format_fit"]}], "not_recommended": [], "summary": "s"}
    client = _install(monkeypatch, [bad, bad])
    assert decide.ai_recommendation(ds, "E0028") is None
    assert client.chat.completions.calls == 2  # retried once


def test_too_few_factor_kinds_falls_back(monkeypatch, ds):
    event_id, valid = _valid_pick(ds)
    thin = {"picks": [{"event_id": event_id, "rationale": "x", "factors_used": ["target_gap", "availability"]}], "not_recommended": [], "summary": "s"}
    _install(monkeypatch, [thin, thin])
    assert decide.ai_recommendation(ds, "E0028") is None


def test_retry_recovers_after_one_bad_answer(monkeypatch, ds):
    event_id, valid = _valid_pick(ds)
    bad = {"picks": [{"event_id": "EV_NOPE", "rationale": "x", "factors_used": ["target_gap", "availability", "format_fit"]}], "not_recommended": [], "summary": "s"}
    _install(monkeypatch, [bad, valid])
    result = decide.ai_recommendation(ds, "E0028")
    assert result is not None and result.recommendations[0].event_id == event_id


def test_exception_falls_back(monkeypatch, ds):
    _install(monkeypatch, [RuntimeError("timeout")])
    assert decide.ai_recommendation(ds, "E0028") is None


def test_disabled_client_returns_none(monkeypatch, ds):
    monkeypatch.setattr(decide, "get_client", lambda: None)
    assert decide.ai_recommendation(ds, "E0028") is None


def test_calling_a_non_critical_skill_critical_is_rejected(monkeypatch, ds):
    from app.llm.prompt import build_context
    built = build_context(ds, "E0028", None)
    event_id = next(e for e in built["candidate_ids"] if "critical_gap" not in built["factor_kinds_by_event"][e])
    kinds = sorted(built["factor_kinds_by_event"][event_id])[:3]
    overclaim = {"picks": [{"event_id": event_id, "rationale": "This closes your critical gap.", "factors_used": kinds}], "not_recommended": [], "summary": "s"}
    honest = {"picks": [{"event_id": event_id, "rationale": "This closes a gap for your next grade.", "factors_used": kinds}], "not_recommended": [], "summary": "s"}
    client = _install(monkeypatch, [overclaim, honest])
    result = decide.ai_recommendation(ds, "E0028")
    assert client.chat.completions.calls == 2  # the overclaim was rejected and retried
    assert result is not None and "critical" not in result.recommendations[0].rationale.lower()
