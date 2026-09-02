from open_webui.utils.payload import (
    apply_model_params_and_system_prompt_to_body,
    apply_model_params_to_body_openai,
    convert_payload_openai_to_ollama,
)


def test_openai_payload_preserves_llama_reasoning_controls():
    payload = apply_model_params_to_body_openai(
        {
            "reasoning_effort": "none",
            "reasoning_budget_tokens": "0",
            "thinking_budget_tokens": "12",
            "reasoning_format": "deepseek",
            "reasoning_control": True,
        },
        {"model": "local-model"},
    )

    assert payload["reasoning_effort"] == "none"
    assert payload["reasoning_budget_tokens"] == 0
    assert payload["thinking_budget_tokens"] == 12
    assert payload["reasoning_format"] == "deepseek"
    assert payload["reasoning_control"] is True


def test_persona_system_prompt_applies_without_model_params():
    payload = apply_model_params_and_system_prompt_to_body(
        {},
        {
            "model": "passthrough-model",
            "messages": [{"role": "user", "content": "Who are you?"}],
        },
        {
            "system_prompt_override_present": True,
            "system_prompt_override": "You are Aunt Gemma.",
        },
        None,
        apply_model_params_to_body_openai,
    )

    assert payload["messages"] == [
        {"role": "system", "content": "You are Aunt Gemma."},
        {"role": "user", "content": "Who are you?"},
    ]


def test_persona_system_prompt_overrides_model_prompt_and_keeps_model_params():
    payload = apply_model_params_and_system_prompt_to_body(
        {"system": "Base model prompt", "temperature": "0.7"},
        {
            "model": "configured-model",
            "messages": [{"role": "user", "content": "Who are you?"}],
        },
        {
            "system_prompt_override_present": True,
            "system_prompt_override": "You are Aunt Gemma.",
        },
        None,
        apply_model_params_to_body_openai,
    )

    assert payload["temperature"] == 0.7
    assert payload["messages"][0] == {
        "role": "system",
        "content": "You are Aunt Gemma.",
    }


def test_bypass_system_prompt_preserves_passthrough_messages():
    messages = [{"role": "user", "content": "Who are you?"}]
    payload = apply_model_params_and_system_prompt_to_body(
        {},
        {"model": "passthrough-model", "messages": list(messages)},
        {
            "system_prompt_override_present": True,
            "system_prompt_override": "You are Aunt Gemma.",
        },
        None,
        apply_model_params_to_body_openai,
        bypass_system_prompt=True,
    )

    assert payload["messages"] == messages


def test_openai_to_ollama_conversion_preserves_input_payload():
    metadata = {"request_id": object(), "tags": ["local"]}
    payload = {
        "model": "local-model",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": True,
        "metadata": metadata,
        "options": {
            "format": '{"type":"object"}',
            "keep_alive": "5m",
            "think": False,
            "max_tokens": 12,
            "system": "internal rule",
            "temperature": 0.3,
        },
        "stop": ["</s>"],
    }
    original_options = dict(payload["options"])

    converted = convert_payload_openai_to_ollama(payload)

    assert payload["options"] == original_options
    assert payload["metadata"] is metadata
    assert converted["metadata"] == metadata
    assert converted["metadata"] is not metadata
    assert converted["format"] == {"type": "object"}
    assert converted["keep_alive"] == "5m"
    assert converted["think"] is False
    assert converted["system"] == "internal rule"
    assert converted["options"]["num_predict"] == 12
    assert converted["options"]["temperature"] == 0.3
    assert converted["options"]["stop"] == ["</s>"]
    assert "max_tokens" not in converted["options"]
