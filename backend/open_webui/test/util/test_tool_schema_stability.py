from types import SimpleNamespace

import pytest

from open_webui.utils import tools


def test_clean_openai_tool_schema_sorts_required_fields_recursively():
    cleaned = tools.clean_openai_tool_schema(
        {
            "name": "send_process_input",
            "parameters": {
                "type": "object",
                "required": ["process_id", "input", "process_id"],
                "properties": {
                    "nested": {
                        "type": "object",
                        "required": ["z", "a"],
                        "properties": {
                            "a": {"type": "string"},
                            "z": {"type": "string"},
                        },
                    }
                },
            },
        }
    )

    assert cleaned["parameters"]["required"] == ["input", "process_id"]
    assert cleaned["parameters"]["properties"]["nested"]["required"] == ["a", "z"]


def test_convert_openapi_to_tool_payload_has_stable_required_order():
    payload = tools.convert_openapi_to_tool_payload(
        {
            "paths": {
                "/input": {
                    "post": {
                        "operationId": "send_process_input",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["process_id", "input"],
                                        "properties": {
                                            "process_id": {"type": "string"},
                                            "input": {"type": "string"},
                                        },
                                    }
                                }
                            }
                        },
                    }
                }
            }
        }
    )

    assert payload[0]["parameters"]["required"] == ["input", "process_id"]


@pytest.mark.asyncio
async def test_get_terminal_servers_reuses_app_state(monkeypatch):
    cached = [{"id": "terminal", "specs": []}]
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(TERMINAL_SERVERS=cached, redis=None))
    )

    async def unexpected_reload(_request):
        raise AssertionError("cached terminal specs should not be fetched again")

    monkeypatch.setattr(tools, "set_terminal_servers", unexpected_reload)

    assert await tools.get_terminal_servers(request) is cached
