<script lang="ts">
	import { pctFrac } from '$lib/format';

	interface Props {
		label: string;
		/** Current value in [0,1]. */
		value: number;
		/** Optional threshold marker in [0,1]. */
		threshold?: number;
		/** Colour intent for the fill. */
		tone?: 'accent' | 'good' | 'warn' | 'bad' | 'auto';
	}

	let { label, value, threshold, tone = 'auto' }: Props = $props();

	const v = $derived(Math.max(0, Math.min(1, value)));
	const breached = $derived(threshold !== undefined && value > threshold);
	const resolvedTone = $derived.by(() => {
		if (tone !== 'auto') return tone;
		if (breached) return 'bad';
		if (threshold !== undefined && value > threshold * 0.75) return 'warn';
		return 'good';
	});
</script>

<div class="metric">
	<div class="head">
		<span class="label">{label}</span>
		<span class="val mono" class:breached>{pctFrac(value)}</span>
	</div>
	<div class="track">
		<div class="fill {resolvedTone}" style:width="{v * 100}%"></div>
		{#if threshold !== undefined}
			<div class="threshold" style:left="{Math.min(1, threshold) * 100}%" title="limit {pctFrac(threshold)}"></div>
		{/if}
	</div>
</div>

<style>
	.metric {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		font-size: 12px;
	}
	.label {
		color: var(--text-muted);
	}
	.val {
		font-weight: 600;
		font-size: 12px;
	}
	.val.breached {
		color: var(--critical);
	}
	.track {
		position: relative;
		height: 6px;
		border-radius: 999px;
		background: var(--surface-3);
		overflow: visible;
	}
	.fill {
		position: absolute;
		inset: 0 auto 0 0;
		border-radius: 999px;
		transition: width 0.5s ease;
	}
	.fill.good {
		background: linear-gradient(90deg, var(--accent), var(--ok));
	}
	.fill.accent {
		background: var(--aurora-gradient);
	}
	.fill.warn {
		background: linear-gradient(90deg, var(--warn), #ffd166);
	}
	.fill.bad {
		background: linear-gradient(90deg, #ff7a5c, var(--critical));
	}
	.threshold {
		position: absolute;
		top: -2px;
		bottom: -2px;
		width: 2px;
		background: var(--text);
		opacity: 0.5;
		transform: translateX(-1px);
	}
</style>
