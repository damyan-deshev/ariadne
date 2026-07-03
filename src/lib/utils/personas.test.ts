import { describe, expect, it } from 'vitest';

import { getPersonaRuntimeParamDefaults } from './personas';

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
					chat_template_kwargs: { enable_thinking: false }
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
			chat_template_kwargs: { enable_thinking: false }
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
