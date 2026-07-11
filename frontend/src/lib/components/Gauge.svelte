<script lang="ts">
	interface Props {
		/** Value in [0,1]. */
		value: number;
		label?: string;
		center?: string;
		tone?: 'accent' | 'good' | 'warn' | 'bad';
		size?: number;
	}

	let { value, label, center, tone = 'accent', size = 132 }: Props = $props();

	const r = 46;
	const cx = 56;
	const cy = 52;
	const len = Math.PI * r;
	const v = $derived(Math.max(0, Math.min(1, value)));
	const dash = $derived(`${(v * len).toFixed(2)} ${len.toFixed(2)}`);
	const stroke = $derived.by(() => {
		switch (tone) {
			case 'good':
				return 'var(--ok)';
			case 'warn':
				return 'var(--warn)';
			case 'bad':
				return 'var(--critical)';
			default:
				return 'var(--accent)';
		}
	});
</script>

<div class="gauge" style:width="{size}px">
	<svg viewBox="0 0 112 64" width={size} height={size * 0.57} aria-hidden="true">
		<path
			d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}"
			fill="none"
			stroke="var(--surface-3)"
			stroke-width="8"
			stroke-linecap="round"
		/>
		<path
			d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}"
			fill="none"
			stroke={stroke}
			stroke-width="8"
			stroke-linecap="round"
			stroke-dasharray={dash}
			style="transition: stroke-dasharray 0.6s ease;"
		/>
	</svg>
	<div class="readout">
		<span class="center mono" style:color={stroke}>{center ?? `${Math.round(v * 100)}%`}</span>
		{#if label}<span class="label">{label}</span>{/if}
	</div>
</div>

<style>
	.gauge {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
	}
	svg {
		display: block;
	}
	.readout {
		margin-top: -18px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
	}
	.center {
		font-size: 22px;
		font-weight: 700;
		letter-spacing: -0.02em;
	}
	.label {
		font-size: 11px;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}
</style>
