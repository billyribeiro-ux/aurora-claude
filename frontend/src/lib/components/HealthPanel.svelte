<script lang="ts">
	import Card from './Card.svelte';
	import Badge from './Badge.svelte';
	import MetricBar from './MetricBar.svelte';
	import type { HealthReport } from '$lib/types';

	interface Props {
		health: HealthReport;
	}

	let { health }: Props = $props();

	type Variant = 'ok' | 'info' | 'warn' | 'critical';
	const statusVariant: Variant = $derived.by(() => {
		switch (health.status) {
			case 'HEALTHY':
				return 'ok';
			case 'WATCH':
				return 'info';
			case 'DEGRADED':
				return 'warn';
			case 'HALT':
				return 'critical';
		}
	});
</script>

<Card eyebrow="Self-Monitoring · illustrative" title="System Health">
	{#snippet action()}
		<Badge variant={statusVariant} dot pulse={health.status !== 'HEALTHY'}>{health.status}</Badge>
	{/snippet}

	<div class="bars">
		<MetricBar label="Drawdown" value={health.metrics.drawdown} threshold={0.15} />
		<MetricBar label="Model uncertainty" value={health.metrics.uncertainty} threshold={0.8} />
		<MetricBar label="Reward decay" value={health.metrics.rewardDecay} threshold={0.2} />
		<MetricBar label="Model drift" value={health.metrics.drift} threshold={0.3} />
		<MetricBar label="Portfolio heat" value={health.metrics.portfolioHeat} threshold={1} tone="accent" />
	</div>

	<div class="alerts">
		{#if health.alerts.length === 0}
			<div class="clear">
				<span class="tick">✓</span> All monitors within tolerance
			</div>
		{:else}
			{#each health.alerts as alert (alert)}
				<div class="alert">
					<span class="siren">▲</span>
					<span class="mono">{alert}</span>
				</div>
			{/each}
		{/if}
	</div>
</Card>

<style>
	.bars {
		display: flex;
		flex-direction: column;
		gap: 14px;
	}
	.alerts {
		margin-top: 16px;
		border-top: 1px solid var(--border);
		padding-top: 14px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.clear {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 13px;
		color: var(--text-muted);
	}
	.tick {
		color: var(--ok);
		font-weight: 700;
	}
	.alert {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 12px;
		color: var(--critical);
		background: var(--short-soft);
		border: 1px solid rgba(255, 95, 115, 0.25);
		border-radius: var(--radius-sm);
		padding: 8px 10px;
	}
	.siren {
		font-size: 10px;
	}
</style>
