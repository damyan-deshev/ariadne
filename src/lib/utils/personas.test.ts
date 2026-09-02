import { describe, expect, it } from 'vitest';

import { getEffectivePersonaState, getPersonaRuntimeParamDefaults } from './personas';

describe('persona runtime param defaults', () => {
	it('extracts structured runtime defaults for the CBT lane', () => {
		expect(
			getPersonaRuntimeParamDefaults({
				runtime_defaults: {
					working_mode: 'CBT',
					local_corpus_mode: 'prefer',
					science_research_mode: 'deep',
					science_attached_corpora: ['Medicine', ''],
					temperature: '0.7',
					top_p: 0.8,
					top_k: '20',
					min_p: 0,
					presence_penalty: 1.5,
					repeat_penalty: 1,
					reasoning_effort: 'none',
					reasoning_budget_tokens: '0',
					chat_template_kwargs: { enable_thinking: true }
				},
				cbt_persona: true
			})
		).toEqual({
			working_mode: 'cbt',
			local_corpus_mode: 'prefer',
			science_research_mode: 'deep',
			science_attached_corpora: ['medicine'],
			temperature: 0.7,
			top_p: 0.8,
			top_k: 20,
			min_p: 0,
			presence_penalty: 1.5,
			repeat_penalty: 1,
			reasoning_effort: 'none',
			reasoning_budget_tokens: 0,
			chat_template_kwargs: { enable_thinking: true }
		});
	});

	it('keeps legacy working-mode capabilities as fallback values', () => {
		expect(
			getPersonaRuntimeParamDefaults({
				preferred_working_mode: 'cbt',
				preferred_local_corpus_mode: 'prefer'
			})
		).toEqual({
			working_mode: 'cbt',
			local_corpus_mode: 'prefer'
		});
	});
});

describe('persona system prompt overrides', () => {
	const persona = {
		id: 'aunt-gemma',
		name: 'Aunt Gemma',
		system_prompt: 'You are Aunt Gemma.',
		tool_ids: [],
		skill_ids: [],
		filter_ids: [],
		action_ids: [],
		default_feature_ids: [],
		capabilities: {}
	} as any;

	it('treats a legacy null chat override as no system prompt override', () => {
		const state = getEffectivePersonaState({
			persona,
			chatMeta: {
				persona_defaults_snapshot: { ...persona },
				persona_chat_overrides: { system_prompt: null }
			},
			tools: [],
			functions: []
		});

		expect(state?.effective.system_prompt).toBe('You are Aunt Gemma.');
	});

	it('preserves an empty string as an intentional system prompt override', () => {
		const state = getEffectivePersonaState({
			persona,
			chatMeta: {
				persona_defaults_snapshot: { ...persona },
				persona_chat_overrides: { system_prompt: '' }
			},
			tools: [],
			functions: []
		});

		expect(state?.effective.system_prompt).toBe('');
	});
});
