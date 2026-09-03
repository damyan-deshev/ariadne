from types import SimpleNamespace

from open_webui.routers.audio import (
    SUPERTONIC_VOICE_NAMES,
    get_available_models,
    get_available_voices,
)


def _request(tts_engine: str):
    config = SimpleNamespace(TTS_ENGINE=tts_engine)
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(config=config)))


def test_supertonic_global_default_exposes_its_model(monkeypatch):
    monkeypatch.setenv("AUDIO_TTS_SUPERTONIC_MODEL", "custom-supertonic")

    assert get_available_models(_request("supertonic")) == [
        {"id": "custom-supertonic"}
    ]


def test_supertonic_global_default_exposes_all_named_voices():
    assert get_available_voices(_request("supertonic")) == SUPERTONIC_VOICE_NAMES
