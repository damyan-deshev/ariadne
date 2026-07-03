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
					science_attached_corpora: ['Medicine', '']
				},
				cbt_persona: true
			})
		).toEqual({
			working_mode: 'cbt',
			local_corpus_mode: 'prefer',
			science_research_mode: 'deep',
			science_attached_corpora: ['medicine']
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
