"""Small helpers shared by Ariadne's local speech providers."""

from __future__ import annotations

import io
import re
import unicodedata
import wave
from collections.abc import Sequence


_WORD_OR_SPACE_RE = re.compile(r"\s+|[^\s]+", re.UNICODE)
_CYRILLIC_RE = re.compile(r"[\u0400-\u052f]")
_LATIN_RE = re.compile(r"[A-Za-z]")

# Supertonic 3 normalizes several typographic characters internally, but its
# validator runs before synthesis and still rejects some common variants. Keep
# this compatibility layer provider-specific so other TTS engines continue to
# receive their existing input unchanged.
_SUPERTONIC_CHARACTER_REPLACEMENTS = str.maketrans(
    {
        "„": '"',  # Bulgarian opening double quote
        "“": '"',
        "”": '"',
        "«": '"',
        "»": '"',
        "″": '"',
        "‚": "'",
        "‘": "'",
        "’": "'",
        "′": "'",
        "´": "'",
        "`": "'",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "−": "-",
        " ": " ",
        " ": " ",
        " ": " ",
        "​": "",
        "‌": "",
        "‍": "",
        "﻿": "",
        "­": "",
        "…": "...",
        "•": "-",
        "‣": "-",
        "◦": "-",
        "⁃": "-",
        "·": " ",
        "·": " ",
        "⋅": " ",
        "‰": "%",
        "‡": "",
        "≠": "!=",
        "≤": "<=",
        "≥": ">=",
        "∑": "sum",
        "↔": "<->",
        "⇒": "=>",
    }
)


def split_bg_en_runs(text: str) -> list[tuple[str, str]]:
    """Split mixed Cyrillic/Latin text into Supertonic language runs.

    Supertonic 3 accepts one language token per synthesis request. Its ``na``
    fallback is useful for unknown text, but a single mixed Bulgarian/English
    request can corrupt one of the scripts. Keeping whitespace and punctuation
    attached to the surrounding word runs lets callers synthesize each run with
    the right token and concatenate the resulting PCM without changing text.
    """

    if not text or not text.strip():
        return []

    runs: list[tuple[str, str]] = []
    current_language: str | None = None
    current_parts: list[str] = []

    for part in _WORD_OR_SPACE_RE.findall(text):
        cyrillic_count = len(_CYRILLIC_RE.findall(part))
        latin_count = len(_LATIN_RE.findall(part))

        language: str | None = None
        if cyrillic_count or latin_count:
            language = "bg" if cyrillic_count >= latin_count else "en"

        if language is None or current_language in {None, language}:
            current_parts.append(part)
            if language is not None:
                current_language = language
            continue

        segment = "".join(current_parts).strip()
        if segment:
            runs.append((current_language, segment))
        current_language = language
        current_parts = [part]

    segment = "".join(current_parts).strip()
    if segment:
        runs.append((current_language or "na", segment))

    return runs


def normalize_supertonic_text(text: str) -> str:
    """Normalize common text variants rejected by Supertonic 3.

    The installed model's tokenizer is authoritative here. This deliberately
    translates punctuation and semantic symbols instead of using a broad
    ASCII allowlist, which would silently destroy Cyrillic, diacritics,
    currencies, units, and mathematical content. Remaining Unicode control
    characters are never speakable and are safe to discard.
    """

    if not text:
        return ""

    normalized = unicodedata.normalize("NFC", text).translate(
        _SUPERTONIC_CHARACTER_REPLACEMENTS
    )
    normalized = "".join(
        character
        for character in normalized
        if character in "\n\t" or not unicodedata.category(character).startswith("C")
    )
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return normalized.strip()


def concatenate_wav_bytes(parts: Sequence[bytes]) -> bytes:
    """Concatenate compatible PCM WAV payloads and return one valid WAV."""

    if not parts:
        raise ValueError("At least one WAV payload is required")
    if len(parts) == 1:
        return parts[0]

    output = io.BytesIO()
    expected_format: tuple[int, int, int, str] | None = None
    frames: list[bytes] = []

    for payload in parts:
        with wave.open(io.BytesIO(payload), "rb") as source:
            audio_format = (
                source.getnchannels(),
                source.getsampwidth(),
                source.getframerate(),
                source.getcomptype(),
            )
            if expected_format is None:
                expected_format = audio_format
            elif audio_format != expected_format:
                raise ValueError(
                    "Cannot concatenate WAV payloads with different audio formats"
                )
            frames.append(source.readframes(source.getnframes()))

    assert expected_format is not None
    channels, sample_width, sample_rate, compression_type = expected_format
    with wave.open(output, "wb") as destination:
        destination.setnchannels(channels)
        destination.setsampwidth(sample_width)
        destination.setframerate(sample_rate)
        destination.setcomptype(compression_type, "not compressed")
        destination.writeframes(b"".join(frames))

    return output.getvalue()
