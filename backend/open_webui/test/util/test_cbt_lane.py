from types import SimpleNamespace

import open_webui.utils.personas as persona_utils


def test_cbt_therapist_persona_form_uses_cbt_runtime_defaults():
    form = persona_utils.build_cbt_therapist_persona_form(
        SimpleNamespace(CBT_THERAPIST_MODEL="Qwen3.6-27B-MTP-Q6_K")
    )

    assert form.name == "CBT Therapist"
    assert form.bound_model_id == "Qwen3.6-27B-MTP-Q6_K"
    assert form.archetype == "coach"
    assert form.capabilities["preferred_working_mode"] == "cbt"
    assert form.capabilities["preferred_local_corpus_mode"] == "prefer"
    assert form.capabilities["cbt_persona"] is True
    assert form.capabilities["vendor_sampling_profile"] == "qwen3.6-27b-non-thinking"
    assert form.capabilities["runtime_defaults"] == {
        "working_mode": "cbt",
        "local_corpus_mode": "prefer",
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repeat_penalty": 1.0,
        "reasoning_effort": "none",
        "reasoning_budget_tokens": 0,
    }
    assert "self-harm, plan, intent, means" in form.system_prompt
    assert "Do not merge CBT corpus evidence with the medical or offsec corpora" in (
        form.system_prompt
    )


def test_persona_runtime_defaults_include_sampling_and_reasoning_controls():
    defaults = persona_utils.get_persona_runtime_param_defaults(
        {
            "capabilities": {
                "runtime_defaults": {
                    "working_mode": "cbt",
                    "local_corpus_mode": "prefer",
                    "temperature": "0.7",
                    "top_p": 0.8,
                    "top_k": "20",
                    "min_p": 0,
                    "presence_penalty": 1.5,
                    "repeat_penalty": 1,
                    "reasoning_effort": "none",
                    "reasoning_budget_tokens": "0",
                    "ignored": "value",
                }
            }
        }
    )

    assert defaults == {
        "working_mode": "cbt",
        "local_corpus_mode": "prefer",
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repeat_penalty": 1.0,
        "reasoning_effort": "none",
        "reasoning_budget_tokens": 0,
    }


def test_apply_persona_runtime_defaults_preserves_explicit_chat_params():
    defaults = {
        "working_mode": "cbt",
        "local_corpus_mode": "prefer",
        "temperature": 0.7,
        "top_p": 0.8,
        "reasoning_effort": "none",
        "reasoning_budget_tokens": 0,
    }

    params = persona_utils.apply_persona_runtime_param_defaults_to_chat_params(
        {
            "working_mode": "general",
            "temperature": 0.2,
            "reasoning_effort": "high",
            "chat_template_kwargs": {"enable_thinking": True},
        },
        defaults,
    )

    assert params == {
        "working_mode": "general",
        "temperature": 0.2,
        "top_p": 0.8,
        "reasoning_effort": "high",
        "reasoning_budget_tokens": 0,
        "chat_template_kwargs": {"enable_thinking": True},
    }


def test_null_chat_system_prompt_override_preserves_persona_snapshot():
    requested = persona_utils._merge_requested_state(
        {"system_prompt": "You are Aunt Gemma."},
        {"system_prompt": None},
    )

    assert requested["system_prompt"] == "You are Aunt Gemma."


def test_empty_chat_system_prompt_override_intentionally_disables_persona_prompt():
    requested = persona_utils._merge_requested_state(
        {"system_prompt": "You are Aunt Gemma."},
        {"system_prompt": ""},
    )

    assert requested["system_prompt"] == ""
