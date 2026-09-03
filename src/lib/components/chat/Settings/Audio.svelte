<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onDestroy, onMount, getContext } from 'svelte';

	import { user, settings, config } from '$lib/stores';
	import { getVoices as _getVoices, synthesizeOpenAISpeech } from '$lib/apis/audio';

	import Switch from '$lib/components/common/Switch.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	const dispatch = createEventDispatcher();

	const i18n = getContext('i18n');

	export let saveSettings: Function;

	// Audio
	let conversationMode = false;
	let speechAutoSend = false;
	let responseAutoPlayback = false;
	let nonLocalVoices = false;

	let STTEngine = '';
	let STTLanguage = '';

	let TTSEngine = '';
	let TTSEngineConfig = {};

	let TTSModel = null;
	let TTSModelProgress = null;
	let TTSModelLoading = false;

	let voices = [];
	let voice = '';

	// Audio speed control
	let playbackRate = 1;

	const SUPERTONIC_VOICES = [
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
	];
	const DEFAULT_SUPERTONIC_PREVIEW_TEXT =
		'Здравей! Това е кратък гласов тест. Hello! This is a short voice preview.';
	let supertonicPreviewText = DEFAULT_SUPERTONIC_PREVIEW_TEXT;
	let supertonicPreviewLoading = false;
	let supertonicPreviewAudio: HTMLAudioElement | null = null;
	let supertonicPreviewUrl = '';

	const cleanupSupertonicPreview = () => {
		supertonicPreviewAudio?.pause();
		supertonicPreviewAudio = null;

		if (supertonicPreviewUrl) {
			URL.revokeObjectURL(supertonicPreviewUrl);
			supertonicPreviewUrl = '';
		}
	};

	const previewSupertonicVoice = async () => {
		const previewText = supertonicPreviewText.trim();
		if (!previewText) {
			toast.error($i18n.t('Preview text is required'));
			return;
		}

		supertonicPreviewLoading = true;
		cleanupSupertonicPreview();

		try {
			const res = await synthesizeOpenAISpeech(
				localStorage.token,
				voice || 'M1',
				previewText,
				undefined,
				undefined,
				'supertonic'
			);

			if (!res) {
				return;
			}

			const url = URL.createObjectURL(await res.blob());
			const audio = new Audio(url);
			supertonicPreviewUrl = url;
			audio.onended = cleanupSupertonicPreview;
			audio.onerror = cleanupSupertonicPreview;
			supertonicPreviewAudio = audio;
			await audio.play();
		} catch (error) {
			console.error(error);
			toast.error(`${error}`);
		} finally {
			supertonicPreviewLoading = false;
		}
	};

	const getVoices = async () => {
		if (TTSEngine === 'browser-kokoro') {
			if (!TTSModel) {
				await loadKokoro();
			}

			voices = Object.entries(TTSModel.voices).map(([key, value]) => {
				return {
					id: key,
					name: value.name,
					localService: false
				};
			});
			if (!voices.some((item) => item.id === voice)) {
				const savedVoice = $settings?.audio?.tts?.voice;
				voice = voices.some((item) => item.id === savedVoice) ? savedVoice : (voices[0]?.id ?? '');
			}
		} else if (TTSEngine === 'supertonic') {
			voices = SUPERTONIC_VOICES.map((item) => ({
				...item,
				localService: true
			}));
			if (!voices.some((item) => item.id === voice)) {
				voice = TTSEngineConfig?.voice ?? 'M1';
			}
		} else {
			if ($config.audio.tts.engine === '') {
				const getVoicesLoop = setInterval(async () => {
					voices = await speechSynthesis.getVoices();

					// do your loop
					if (voices.length > 0) {
						clearInterval(getVoicesLoop);
					}
				}, 100);
			} else {
				const res = await _getVoices(localStorage.token).catch((e) => {
					toast.error(`${e}`);
				});

				if (res) {
					console.log(res);
					voices = res.voices;
				}
			}
		}
	};

	const toggleResponseAutoPlayback = async () => {
		responseAutoPlayback = !responseAutoPlayback;
		saveSettings({ responseAutoPlayback: responseAutoPlayback });
	};

	const toggleSpeechAutoSend = async () => {
		speechAutoSend = !speechAutoSend;
		saveSettings({ speechAutoSend: speechAutoSend });
	};

	onMount(async () => {
		playbackRate = $settings.audio?.tts?.playbackRate ?? 1;
		conversationMode = $settings.conversationMode ?? false;
		speechAutoSend = $settings.speechAutoSend ?? false;
		responseAutoPlayback = $settings.responseAutoPlayback ?? false;

		STTEngine = $settings?.audio?.stt?.engine ?? '';
		STTLanguage = $settings?.audio?.stt?.language ?? '';

		TTSEngine = $settings?.audio?.tts?.engine ?? '';
		TTSEngineConfig = $settings?.audio?.tts?.engineConfig ?? {};

		if (TTSEngine === 'supertonic') {
			voice = TTSEngineConfig?.voice ?? 'M1';
		} else if ($settings?.audio?.tts?.defaultVoice === $config.audio.tts.voice) {
			voice = $settings?.audio?.tts?.voice ?? $config.audio.tts.voice ?? '';
		} else {
			voice = $config.audio.tts.voice ?? '';
		}

		nonLocalVoices = $settings.audio?.tts?.nonLocalVoices ?? false;

		await getVoices();
	});

	onDestroy(cleanupSupertonicPreview);

	const onTTSEngineChange = async () => {
		cleanupSupertonicPreview();
		if (TTSEngine === 'browser-kokoro') {
			await loadKokoro();
		} else if (TTSEngine === 'supertonic') {
			await getVoices();
		} else {
			voice = $config.audio.tts.voice ?? '';
			await getVoices();
		}
	};

	const loadKokoro = async () => {
		if (TTSEngine === 'browser-kokoro') {
			voices = [];

			if (TTSEngineConfig?.dtype) {
				TTSModel = null;
				TTSModelProgress = null;
				TTSModelLoading = true;

				try {
					const model_id = 'onnx-community/Kokoro-82M-v1.0-ONNX';
					const dtype = typeof TTSEngineConfig?.dtype === 'string' ? TTSEngineConfig.dtype : 'fp32';
					const devices = !!navigator?.gpu ? ['webgpu', 'wasm'] : ['wasm'];

					const { KokoroTTS } = await import('kokoro-js');

					let lastError = null;
					for (const device of devices) {
						try {
							TTSModel = await KokoroTTS.from_pretrained(model_id, {
								dtype, // Options: "fp32", "fp16", "q8", "q4", "q4f16"
								device,
								progress_callback: (e) => {
									TTSModelProgress = e;
									console.log(e);
								}
							});
							break;
						} catch (error) {
							lastError = error;
							console.warn(`Kokoro settings init failed on ${device}, trying fallback`, error);
						}
					}

					if (!TTSModel) {
						toast.error(`${lastError}`);
						throw lastError;
					}

					await getVoices();
				} finally {
					TTSModelLoading = false;
				}

				// const rawAudio = await tts.generate(inputText, {
				// 	// Use `tts.list_voices()` to list all available voices
				// 	voice: voice
				// });

				// const blobUrl = URL.createObjectURL(await rawAudio.toBlob());
				// const audio = new Audio(blobUrl);

				// audio.play();
			}
		}
	};
</script>

<form
	id="tab-audio"
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={async () => {
		saveSettings({
			audio: {
				stt: {
					engine: STTEngine !== '' ? STTEngine : undefined,
					language: STTLanguage !== '' ? STTLanguage : undefined
				},
				tts: {
					engine: TTSEngine !== '' ? TTSEngine : undefined,
					engineConfig:
						TTSEngine === 'supertonic'
							? { ...TTSEngineConfig, voice: voice || 'M1' }
							: TTSEngineConfig,
					playbackRate: playbackRate,
					voice: voice !== '' ? voice : undefined,
					defaultVoice: $config?.audio?.tts?.voice ?? '',
					nonLocalVoices: $config.audio.tts.engine === '' ? nonLocalVoices : undefined
				}
			}
		});
		dispatch('save');
	}}
>
	<div class=" space-y-3 overflow-y-scroll max-h-[28rem] md:max-h-full">
		<div>
			<div class=" mb-1 text-sm font-medium">{$i18n.t('STT Settings')}</div>

			{#if $config.audio.stt.engine !== 'web'}
				<div class=" py-0.5 flex w-full justify-between">
					<div class=" self-center text-xs font-medium">{$i18n.t('Speech-to-Text Engine')}</div>
					<div class="flex items-center relative">
						<select
							class="w-fit pr-8 rounded-sm px-2 p-1 text-xs bg-transparent outline-hidden text-right"
							bind:value={STTEngine}
							aria-label={$i18n.t('Speech-to-Text Engine')}
							placeholder={$i18n.t('Select an engine')}
						>
							<option value="">{$i18n.t('Default')}</option>
							<option value="parakeet">{$i18n.t('Parakeet (Server)')}</option>
							<option value="web">{$i18n.t('Web API')}</option>
						</select>
					</div>
				</div>

				<div class=" py-0.5 flex w-full justify-between">
					<div class=" self-center text-xs font-medium">{$i18n.t('Language')}</div>

					<div class="flex items-center relative text-xs px-3">
						<Tooltip
							content={$i18n.t(
								'The language of the input audio. Supplying the input language in ISO-639-1 (e.g. en) format will improve accuracy and latency. Leave blank to automatically detect the language.'
							)}
							placement="top"
						>
							<input
								type="text"
								bind:value={STTLanguage}
								aria-label={$i18n.t('Speech-to-Text Language')}
								placeholder={$i18n.t('e.g. en')}
								class=" text-sm text-right bg-transparent dark:text-gray-300 outline-hidden"
							/>
						</Tooltip>
					</div>
				</div>
			{/if}

			<div class=" py-0.5 flex w-full justify-between">
				<div class=" self-center text-xs font-medium">
					{$i18n.t('Instant Auto-Send After Voice Transcription')}
				</div>

				<button
					class="p-1 px-3 text-xs flex rounded-sm transition"
					on:click={() => {
						toggleSpeechAutoSend();
					}}
					type="button"
					role="switch"
					aria-checked={speechAutoSend}
				>
					{#if speechAutoSend === true}
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					{:else}
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					{/if}
				</button>
			</div>
		</div>

		<div>
			<div class=" mb-1 text-sm font-medium">{$i18n.t('TTS Settings')}</div>

			<div class=" py-0.5 flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{$i18n.t('Text-to-Speech Engine')}</div>
				<div class="flex items-center relative">
					<select
						class="w-fit pr-8 rounded-sm px-2 p-1 text-xs bg-transparent outline-hidden text-right"
						bind:value={TTSEngine}
						on:change={onTTSEngineChange}
						aria-label={$i18n.t('Text-to-Speech Engine')}
						placeholder={$i18n.t('Select an engine')}
					>
						<option value="">{$i18n.t('Default')}</option>
						<option value="supertonic">{$i18n.t('Supertonic (Server)')}</option>
						<option value="browser-kokoro">{$i18n.t('Kokoro.js (Browser)')}</option>
					</select>
				</div>
			</div>

			{#if TTSEngine === 'browser-kokoro'}
				<div class=" py-0.5 flex w-full justify-between">
					<div class=" self-center text-xs font-medium">{$i18n.t('Kokoro.js Dtype')}</div>
					<div class="flex items-center relative">
						<select
							class="w-fit pr-8 rounded-sm px-2 p-1 text-xs bg-transparent outline-hidden text-right"
							bind:value={TTSEngineConfig.dtype}
							on:change={loadKokoro}
							aria-label={$i18n.t('Kokoro.js Dtype')}
							placeholder={$i18n.t('Select dtype')}
						>
							<option value="" disabled selected>{$i18n.t('Select dtype')}</option>
							<option value="fp32">fp32</option>
							<option value="fp16">fp16</option>
							<option value="q8">q8</option>
							<option value="q4">q4</option>
						</select>
					</div>
				</div>
			{/if}

			<div class=" py-0.5 flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{$i18n.t('Auto-playback response')}</div>

				<button
					class="p-1 px-3 text-xs flex rounded-sm transition"
					on:click={() => {
						toggleResponseAutoPlayback();
					}}
					type="button"
					role="switch"
					aria-checked={responseAutoPlayback}
				>
					{#if responseAutoPlayback === true}
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					{:else}
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					{/if}
				</button>
			</div>

			<div class=" py-0.5 flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{$i18n.t('Speech Playback Speed')}</div>

				<div class="flex items-center relative text-xs px-3">
					<input
						type="number"
						min="0"
						step="0.01"
						bind:value={playbackRate}
						aria-label={$i18n.t('Speech Playback Speed')}
						class=" text-sm text-right bg-transparent dark:text-gray-300 outline-hidden"
					/>
					x
				</div>
			</div>
		</div>

		<hr class=" border-gray-100/30 dark:border-gray-850/30" />

		{#if TTSEngine === 'supertonic'}
			<div class="space-y-3">
				<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Voice')}</div>
				<div class="flex w-full">
					<div class="flex-1">
						<select
							class="w-full text-sm bg-transparent dark:text-gray-300 outline-hidden"
							bind:value={voice}
							aria-label={$i18n.t('Voice')}
						>
							{#each voices as _voice}
								<option value={_voice.id}>{_voice.name}</option>
							{/each}
						</select>
					</div>
				</div>

				<div>
					<label class="mb-1.5 block text-xs font-medium" for="supertonic-preview-text">
						{$i18n.t('Preview Text')}
					</label>
					<textarea
						id="supertonic-preview-text"
						class="w-full resize-y rounded-lg bg-gray-50 px-3 py-2 text-sm outline-hidden dark:bg-gray-850 dark:text-gray-300"
						rows="3"
						bind:value={supertonicPreviewText}
						placeholder={$i18n.t('Enter a sample text to preview this voice')}
					></textarea>
					<div class="mt-2 flex items-center gap-2">
						<button
							class="flex items-center gap-1.5 rounded-lg bg-gray-100 px-2.5 py-2 text-xs text-gray-800 transition hover:bg-gray-200 disabled:opacity-60 dark:bg-gray-850 dark:text-gray-100 dark:hover:bg-gray-800"
							type="button"
							on:click={previewSupertonicVoice}
							disabled={supertonicPreviewLoading}
						>
							{#if supertonicPreviewLoading}
								<Spinner className="size-3.5" />
								{$i18n.t('Generating preview...')}
							{:else}
								{$i18n.t('Preview Voice')}
							{/if}
						</button>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Uses the selected voice without saving settings first.')}
						</div>
					</div>
				</div>
			</div>
		{:else if TTSEngine === 'browser-kokoro'}
			{#if TTSModel}
				<div>
					<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Voice')}</div>
					<div class="flex w-full">
						<div class="flex-1">
							<input
								list="voice-list"
								class="w-full text-sm bg-transparent dark:text-gray-300 outline-hidden"
								bind:value={voice}
								aria-label={$i18n.t('Voice')}
								placeholder={$i18n.t('Select a voice')}
							/>

							<datalist id="voice-list">
								{#each voices as voice}
									<option value={voice.id}>{voice.name}</option>
								{/each}
							</datalist>
						</div>
					</div>
				</div>
			{:else}
				<div>
					<div class=" mb-2.5 text-sm font-medium flex gap-2 items-center">
						<Spinner className="size-4" />

						<div class=" text-sm font-medium shimmer">
							{$i18n.t('Loading Kokoro.js...')}
							{TTSModelProgress && TTSModelProgress.status === 'progress'
								? `(${Math.round(TTSModelProgress.progress * 10) / 10}%)`
								: ''}
						</div>
					</div>

					<div class="text-xs text-gray-500">
						{$i18n.t('Please do not close the settings page while loading the model.')}
					</div>
				</div>
			{/if}
		{:else if $config.audio.tts.engine === ''}
			<div>
				<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Voice')}</div>
				<div class="flex w-full">
					<div class="flex-1">
						<select
							class="w-full text-sm bg-transparent dark:text-gray-300 outline-hidden"
							bind:value={voice}
							aria-label={$i18n.t('Voice')}
						>
							<option value="" selected={voice !== ''}>{$i18n.t('Default')}</option>
							{#each voices.filter((v) => nonLocalVoices || v.localService === true) as _voice}
								<option
									value={_voice.name}
									class="bg-gray-100 dark:bg-gray-700"
									selected={voice === _voice.name}>{_voice.name}</option
								>
							{/each}
						</select>
					</div>
				</div>
				<div class="flex items-center justify-between my-1.5">
					<div class="text-xs">
						{$i18n.t('Allow non-local voices')}
					</div>

					<div class="mt-1">
						<Switch bind:state={nonLocalVoices} />
					</div>
				</div>
			</div>
		{:else if $config.audio.tts.engine !== ''}
			<div>
				<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Voice')}</div>
				<div class="flex w-full">
					<div class="flex-1">
						<input
							list="voice-list"
							class="w-full text-sm bg-transparent dark:text-gray-300 outline-hidden"
							bind:value={voice}
							aria-label={$i18n.t('Voice')}
							placeholder={$i18n.t('Select a voice')}
						/>

						<datalist id="voice-list">
							{#each voices as voice}
								<option value={voice.id}>{voice.name}</option>
							{/each}
						</datalist>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			type="submit"
		>
			{$i18n.t('Save')}
		</button>
	</div>
</form>
