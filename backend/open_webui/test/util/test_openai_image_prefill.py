import pytest

from open_webui.routers import openai


class _FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    async def json(self):
        return self._body


class _FakeSession:
    def __init__(self, responses, calls):
        self.responses = responses
        self.calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, url, **kwargs):
        self.calls.append(("GET", url, None))
        return self.responses.pop(0)

    async def post(self, url, json=None, **kwargs):
        self.calls.append(("POST", url, json))
        return self.responses.pop(0)


def test_llama_cpp_root_url_only_removes_v1_suffix():
    assert openai._llama_cpp_root_url("http://llama.test:1234/v1") == "http://llama.test:1234"
    assert openai._llama_cpp_root_url("http://llama.test:1234/v1/") == "http://llama.test:1234"
    assert openai._llama_cpp_root_url("http://provider.test/api") == "http://provider.test/api"


def test_extract_image_prefill_data_preserves_message_order():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,FIRST"},
                },
                {"type": "text", "text": "question"},
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,SECOND"},
                }
            ],
        },
    ]

    assert openai._extract_image_prefill_data(messages) == ["FIRST", "SECOND"]


def test_extract_image_prefill_data_rejects_remote_urls():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.test/image.png"},
                }
            ],
        }
    ]

    assert openai._extract_image_prefill_data(messages) == []


@pytest.mark.asyncio
async def test_generate_llama_cpp_image_prefill_stops_after_last_media(monkeypatch):
    marker = "<__media_TEST__>"
    calls = []
    responses = [
        _FakeResponse(200, {"media_marker": marker}),
        _FakeResponse(200, [{"id": 0, "is_processing": False}]),
        _FakeResponse(
            200,
            {
                "prompt": (
                    f"<|im_start|>user\n{marker}{marker}mutable question"
                    "<|im_end|>\n<|im_start|>assistant\n"
                )
            },
        ),
        _FakeResponse(
            200,
            {"timings": {"cache_n": 7, "prompt_n": 99, "prompt_ms": 123.0}},
        ),
    ]
    monkeypatch.setattr(
        openai.aiohttp,
        "ClientSession",
        lambda **kwargs: _FakeSession(responses, calls),
    )
    openai._IMAGE_PREFILL_CAPABILITY_CACHE.clear()
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,FIRST"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,SECOND"},
                    },
                    {"type": "text", "text": "mutable question"},
                ],
            }
        ],
        "tools": [{"type": "function", "function": {"name": "probe"}}],
        "chat_template_kwargs": {"enable_thinking": False},
    }

    result = await openai._generate_llama_cpp_image_prefill(
        url="http://llama.test:1234/v1",
        payload=payload,
        headers={},
        cookies={},
    )

    assert result == {
        "status": True,
        "prefilled": True,
        "cached_tokens": 7,
        "evaluated_tokens": 99,
        "prompt_ms": 123.0,
    }
    assert [call[:2] for call in calls] == [
        ("GET", "http://llama.test:1234/props"),
        ("GET", "http://llama.test:1234/slots?fail_on_no_slot=1"),
        ("POST", "http://llama.test:1234/apply-template"),
        ("POST", "http://llama.test:1234/completion"),
    ]
    completion_payload = calls[-1][2]
    assert completion_payload["prompt"]["prompt_string"].endswith(marker)
    assert "mutable question" not in completion_payload["prompt"]["prompt_string"]
    assert completion_payload["prompt"]["multimodal_data"] == ["FIRST", "SECOND"]
    assert completion_payload["n_predict"] == 0
    assert completion_payload["cache_prompt"] is True


@pytest.mark.asyncio
async def test_generate_llama_cpp_image_prefill_is_noop_when_busy(monkeypatch):
    calls = []
    responses = [
        _FakeResponse(200, {"media_marker": "<__media_TEST__>"}),
        _FakeResponse(503, {"error": "no slot"}),
    ]
    monkeypatch.setattr(
        openai.aiohttp,
        "ClientSession",
        lambda **kwargs: _FakeSession(responses, calls),
    )
    openai._IMAGE_PREFILL_CAPABILITY_CACHE.clear()

    result = await openai._generate_llama_cpp_image_prefill(
        url="http://llama.test:1234/v1",
        payload={
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/png;base64,IMAGE"},
                        }
                    ],
                }
            ]
        },
        headers={},
        cookies={},
    )

    assert result == {"status": True, "prefilled": False, "reason": "busy"}
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_generate_llama_cpp_image_prefill_is_noop_on_provider_error(monkeypatch):
    class BrokenSession(_FakeSession):
        async def get(self, url, **kwargs):
            raise RuntimeError("provider disappeared")

    monkeypatch.setattr(
        openai.aiohttp,
        "ClientSession",
        lambda **kwargs: BrokenSession([], []),
    )
    openai._IMAGE_PREFILL_CAPABILITY_CACHE.clear()

    result = await openai._generate_llama_cpp_image_prefill(
        url="http://llama.test:1234/v1",
        payload={
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/png;base64,IMAGE"},
                        }
                    ],
                }
            ]
        },
        headers={},
        cookies={},
    )

    assert result == {
        "status": True,
        "prefilled": False,
        "reason": "unsupported",
    }
