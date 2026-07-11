<script lang="ts">
	import Card from './Card.svelte';
	import Gauge from './Gauge.svelte';
	import RegimeBadge from './RegimeBadge.svelte';
	import type { RegimeState } from '$lib/types';
	import { num, pctFrac, signed, relative } from '$lib/format';

	interface Props {
		regime: RegimeState;
	}

	let { regime }: Props = $props();

	const trendTone = $derived(regime.trendStrength >= 0 ? 'up' : 'down');
</script>

<Card eyebrow="Market Regime" title="Operating Environment">
	{#snippet action()}
		<RegimeBadge regime={regime.regime} pulse />
	{/snippet}

	<div class="grid">
		<div class="gauge-wrap">
			<Gauge value={regime.confidence} label="confidence" tone="accent" />
			<span class="since">detected {relative(regime.since)}</span>
		</div>

		<div class="stats">
			<div class="stat">
				<span class="k">Trend strength</span>
				<span class="v mono {trendTone}">{signed(regime.trendStrength, 2)}</span>
			</div>
			<div class="stat">
				<span class="k">Breadth</span>
				<span class="v mono">{pctFrac(regime.breadth)}</span>
			</div>
			<div class="stat">
				<span class="k">Implied vol</span>
				<span class="v mono">{num(regime.volatility * 100, 1)}</span>
			</div>
			<div class="stat">
				<span class="k">Exposure cap</span>
				<span class="v mono accent">{pctFrac(regime.exposureCap)}</span>
			</div>
		</div>
	</div>

	<p class="desc">{regime.description}</p>
</Card>

<style>
	.grid {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 20px;
		align-items: center;
	}
	.gauge-wrap {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
	}
	.since {
		font-size: 11px;
		color: var(--text-faint);
	}
	.stats {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 10px 18px;
	}
	.stat {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: 8px 10px;
		background: var(--surface-2);
		border-radius: var(--radius-sm);
		border: 1px solid var(--border);
	}
	.k {
		font-size: 11px;
		color: var(--text-dim);
	}
	.v {
		font-size: 16px;
		font-weight: 600;
	}
	.v.up {
		color: var(--up);
	}
	.v.down {
		color: var(--down);
	}
	.v.accent {
		color: var(--accent);
	}
	.desc {
		margin: 16px 0 0;
		font-size: 13px;
		line-height: 1.6;
		color: var(--text-muted);
		border-top: 1px solid var(--border);
		padding-top: 14px;
	}
	@media (max-width: 520px) {
		.grid {
			grid-template-columns: 1fr;
		}
	}
</style>
