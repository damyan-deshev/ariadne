from open_webui.utils.payload import apply_model_params_to_body_openai


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
