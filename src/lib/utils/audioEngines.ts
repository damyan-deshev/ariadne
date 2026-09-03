export const SUPERTONIC_VOICES = [
	{ id: 'F1', name: 'Mila — female (F1)' },
	{ id: 'F2', name: 'Elena — female (F2)' },
	{ id: 'F3', name: 'Sofia — female (F3)' },
	{ id: 'F4', name: 'Raya — female (F4)' },
	{ id: 'F5', name: 'Nora — female (F5)' },
	{ id: 'M1', name: 'Alex — male (M1)' },
	{ id: 'M2', name: 'Boris — male (M2)' },
	{ id: 'M3', name: 'Viktor — male (M3)' },
	{ id: 'M4', name: 'Martin — male (M4)' },
	{ id: 'M5', name: 'Nikola — male (M5)' }
] as const;

const STT_ENGINE_LABELS: Record<string, string> = {
	'': 'Whisper (Local)',
	parakeet: 'Parakeet (Server)',
	openai: 'OpenAI',
	web: 'Web API',
	deepgram: 'Deepgram',
	azure: 'Azure AI Speech',
	mistral: 'MistralAI'
};

const TTS_ENGINE_LABELS: Record<string, string> = {
	'': 'Web API',
	supertonic: 'Supertonic (Server)',
	transformers: 'Transformers (Local)',
	openai: 'OpenAI',
	kokoro_onnx: 'Kokoro ONNX (Local)',
	omnivoice: 'OmniVoice (Local)',
	elevenlabs: 'ElevenLabs',
	azure: 'Azure AI Speech'
};

export const getSTTEngineLabel = (engine: string | null | undefined) =>
	STT_ENGINE_LABELS[engine ?? ''] ?? engine ?? 'Unknown';

export const getTTSEngineLabel = (engine: string | null | undefined) =>
	TTS_ENGINE_LABELS[engine ?? ''] ?? engine ?? 'Unknown';
