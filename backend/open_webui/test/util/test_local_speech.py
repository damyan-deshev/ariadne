import io
import wave

import pytest

from open_webui.utils.local_speech import concatenate_wav_bytes, split_bg_en_runs


def _wav(sample: int, frames: int = 100, sample_rate: int = 16_000) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as destination:
        destination.setnchannels(1)
        destination.setsampwidth(2)
        destination.setframerate(sample_rate)
        destination.writeframes(sample.to_bytes(2, "little", signed=True) * frames)
    return output.getvalue()


def test_split_bg_en_runs_keeps_monolingual_text_in_one_request():
    assert split_bg_en_runs("Здравей, как си днес?") == [
        ("bg", "Здравей, как си днес?")
    ]
    assert split_bg_en_runs("Please open the terminal.") == [
        ("en", "Please open the terminal.")
    ]


def test_split_bg_en_runs_separates_mixed_script_without_losing_words():
    runs = split_bg_en_runs(
        "Здравей, днес тестваме mixed language speech. После продължаваме."
    )

    assert runs == [
        ("bg", "Здравей, днес тестваме"),
        ("en", "mixed language speech."),
        ("bg", "После продължаваме."),
    ]


def test_split_bg_en_runs_uses_language_agnostic_fallback_for_neutral_text():
    assert split_bg_en_runs("123 + 456 = 579") == [("na", "123 + 456 = 579")]
    assert split_bg_en_runs("   ") == []


def test_concatenate_wav_bytes_preserves_format_and_frames():
    combined = concatenate_wav_bytes([_wav(10, 40), _wav(-10, 60)])

    with wave.open(io.BytesIO(combined), "rb") as source:
        assert source.getnchannels() == 1
        assert source.getsampwidth() == 2
        assert source.getframerate() == 16_000
        assert source.getnframes() == 100


def test_concatenate_wav_bytes_rejects_incompatible_formats():
    with pytest.raises(ValueError, match="different audio formats"):
        concatenate_wav_bytes([_wav(1, sample_rate=16_000), _wav(1, sample_rate=44_100)])
