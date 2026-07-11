<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'neutral' | 'accent' | 'long' | 'short' | 'warn' | 'critical' | 'info' | 'ok';

	interface Props {
		variant?: Variant;
		dot?: boolean;
		pulse?: boolean;
		children: Snippet;
	}

	let { variant = 'neutral', dot = false, pulse = false, children }: Props = $props();
</script>

<span class="badge {variant}" class:pulse>
	{#if dot}<span class="dot"></span>{/if}
	{@render children()}
</span>

<style>
	.badge {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 3px 9px;
		border-radius: var(--radius-pill);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.03em;
		line-height: 1.4;
		border: 1px solid transparent;
		white-space: nowrap;
	}
	.dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: currentColor;
	}
	.neutral {
		background: var(--surface-3);
		color: var(--text-muted);
		border-color: var(--border);
	}
	.accent {
		background: var(--accent-soft);
		color: var(--accent);
		border-color: var(--accent-line);
	}
	.long,
	.ok {
		background: var(--long-soft);
		color: var(--long);
		border-color: rgba(47, 224, 138, 0.3);
	}
	.short,
	.critical {
		background: var(--short-soft);
		color: var(--short);
		border-color: rgba(255, 95, 115, 0.3);
	}
	.warn {
		background: var(--warn-soft);
		color: var(--warn);
		border-color: rgba(255, 176, 32, 0.3);
	}
	.info {
		background: var(--info-soft);
		color: var(--info);
		border-color: rgba(86, 182, 255, 0.3);
	}
	.pulse .dot {
		animation: pulse 1.8s ease-in-out infinite;
	}
	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
			box-shadow: 0 0 0 0 currentColor;
		}
		50% {
			opacity: 0.6;
			box-shadow: 0 0 0 3px transparent;
		}
	}
</style>
