import { describe, expect, it } from 'vitest';

import { getSTTEngineLabel, getTTSEngineLabel, SUPERTONIC_VOICES } from './audioEngines';

describe('audio engine presentation', () => {
	it('describes built-in and sidecar system defaults', () => {
		expect(getSTTEngineLabel('')).toBe('Whisper (Local)');
		expect(getSTTEngineLabel('parakeet')).toBe('Parakeet (Server)');
		expect(getTTSEngineLabel('kokoro_onnx')).toBe('Kokoro ONNX (Local)');
		expect(getTTSEngineLabel('supertonic')).toBe('Supertonic (Server)');
	});

	it('keeps all vendor voice ids available', () => {
		expect(SUPERTONIC_VOICES.map(({ id }) => id)).toEqual([
			'F1',
			'F2',
			'F3',
			'F4',
			'F5',
			'M1',
			'M2',
			'M3',
			'M4',
			'M5'
		]);
	});

	it('does not hide future engines behind a generic label', () => {
		expect(getTTSEngineLabel('future-engine')).toBe('future-engine');
	});
});
