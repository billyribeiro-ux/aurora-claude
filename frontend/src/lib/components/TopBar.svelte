<script lang="ts">
	import Badge from './Badge.svelte';
	import type { SystemMode, DataSource } from '$lib/types';

	interface Props {
		mode: SystemMode;
		dataSource: DataSource;
		title: string;
		subtitle?: string;
	}

	let { mode, dataSource, title, subtitle }: Props = $props();

	let now = $state(new Date());
	let theme = $state<'dark' | 'light'>('dark');

	$effect(() => {
		const stored = localStorage.getItem('aurora-theme');
		if (stored === 'light' || stored === 'dark') {
			theme = stored;
			document.documentElement.dataset.theme = stored;
		}
		const timer = setInterval(() => (now = new Date()), 1000);
		return () => clearInterval(timer);
	});

	function toggleTheme(): void {
		theme = theme === 'dark' ? 'light' : 'dark';
		document.documentElement.dataset.theme = theme;
		localStorage.setItem('aurora-theme', theme);
	}

	const clock = $derived(now.toLocaleTimeString('en-US', { hour12: false }));
	const modeVariant = $derived(mode === 'LIVE' ? 'critical' : mode === 'PAPER' ? 'info' : 'neutral');
</script>

<header class="topbar">
	<div class="titles">
		<h1>{title}</h1>
		{#if subtitle}<p>{subtitle}</p>{/if}
	</div>

	<div class="controls">
		<Badge variant={dataSource === 'FMP' ? 'ok' : 'warn'} dot pulse={dataSource === 'FMP'}>
			{dataSource === 'FMP' ? 'LIVE DATA · FMP' : 'SYNTHETIC DATA'}
		</Badge>
		<Badge variant={modeVariant}>{mode}</Badge>
		<span class="clock mono">{clock}</span>
		<button class="theme" type="button" onclick={toggleTheme} aria-label="Toggle colour theme" title="Toggle theme">
			{#if theme === 'dark'}
				<svg viewBox="0 0 24 24" width="16" height="16"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" /></svg>
			{:else}
				<svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" /></svg>
			{/if}
		</button>
	</div>
</header>

<style>
	.topbar {
		position: sticky;
		top: 0;
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		padding: 16px 28px;
		background: color-mix(in srgb, var(--bg) 78%, transparent);
		backdrop-filter: blur(14px);
		border-bottom: 1px solid var(--border);
	}
	.titles h1 {
		font-size: 20px;
		font-weight: 700;
		letter-spacing: -0.02em;
	}
	.titles p {
		margin: 2px 0 0;
		font-size: 12.5px;
		color: var(--text-dim);
	}
	.controls {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-shrink: 0;
	}
	.clock {
		font-size: 13px;
		font-weight: 600;
		color: var(--text-muted);
		letter-spacing: 0.04em;
	}
	.theme {
		display: grid;
		place-items: center;
		width: 32px;
		height: 32px;
		border-radius: var(--radius-sm);
		border: 1px solid var(--border);
		background: var(--surface-2);
		color: var(--text-muted);
		transition: all 0.15s ease;
	}
	.theme:hover {
		color: var(--text);
		border-color: var(--border-strong);
	}
	@media (max-width: 720px) {
		.topbar {
			padding: 12px 16px;
			flex-wrap: wrap;
		}
		.titles p {
			display: none;
		}
	}
	@media (max-width: 520px) {
		.clock {
			display: none;
		}
	}
</style>
