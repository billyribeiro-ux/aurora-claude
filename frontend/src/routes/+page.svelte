<script lang="ts">
	import { browser } from '$app/environment';
	import type { PageServerData } from './$types';
	import type { DashboardSnapshot } from '$lib/types';
	import { currency, num, pct, pctFrac, clock } from '$lib/format';
	import Card from '$lib/components/Card.svelte';
	import StatTile from '$lib/components/StatTile.svelte';
	import PipelineFlow from '$lib/components/PipelineFlow.svelte';
	import RegimePanel from '$lib/components/RegimePanel.svelte';
	import HealthPanel from '$lib/components/HealthPanel.svelte';
	import SignalsTable from '$lib/components/SignalsTable.svelte';
	import EventLog from '$lib/components/EventLog.svelte';

	interface Props {
		data: PageServerData;
	}

	let { data }: Props = $props();

	// Local live-override state falls back to the server-rendered snapshot.
	let liveSnapshot = $state<DashboardSnapshot | null>(null);
	let live = $state(true);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let lastUpdated = $state(0);

	const snapshot = $derived(liveSnapshot ?? data.snapshot);
	const status = $derived(snapshot.status);
	const signals = $derived(snapshot.signals);
	const portfolio = $derived(status.portfolio);
	const approved = $derived(signals.filter((s) => s.approved).length);
	const dayPnlValue = $derived(
		`${portfolio.dayPnl >= 0 ? '+' : '−'}${currency(Math.abs(portfolio.dayPnl))}`
	);
	const updatedAt = $derived(lastUpdated ? clock(new Date(lastUpdated).toISOString()) : '—');

	async function refresh(): Promise<void> {
		if (!browser || loading) return;
		loading = true;
		try {
			const res = await fetch('/api/status', { headers: { accept: 'application/json' } });
			if (!res.ok) throw new Error(`status ${res.status}`);
			liveSnapshot = (await res.json()) as DashboardSnapshot;
			lastUpdated = Date.now();
			error = null;
		} catch (err) {
			error = err instanceof Error ? err.message : 'refresh failed';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		lastUpdated = Date.now();
		if (!live) return;
		const timer = setInterval(refresh, 20_000);
		return () => clearInterval(timer);
	});
</script>

<div class="page">
	<div class="controls">
		<button class="live" type="button" class:on={live} onclick={() => (live = !live)}>
			<span class="dot"></span>
			{live ? 'Live' : 'Paused'}
		</button>
		<button class="refresh" type="button" onclick={refresh} disabled={loading}>
			{loading ? 'Refreshing…' : 'Refresh'}
		</button>
		<span class="updated">updated <span class="mono">{updatedAt}</span></span>
		{#if error}<span class="err">· {error}</span>{/if}
	</div>

	<div class="kpis">
		<StatTile
			label="Portfolio Equity"
			value={currency(portfolio.equity)}
			delta={portfolio.totalReturnPct}
			sub="paper · total return"
			tone="accent"
		/>
		<StatTile
			label="Day P&L"
			value={dayPnlValue}
			delta={portfolio.dayPnlPct}
			tone={portfolio.dayPnl >= 0 ? 'up' : 'down'}
		/>
		<StatTile
			label="Net Exposure"
			value={pctFrac(portfolio.netExposure)}
			sub="gross {pctFrac(portfolio.grossExposure)}"
		/>
		<StatTile
			label="Open Positions"
			value={String(portfolio.openPositions)}
			sub="{approved}/{signals.length} approved"
		/>
		<StatTile label="Sharpe" value={num(portfolio.sharpe, 2)} sub="sortino {num(portfolio.sortino, 2)}" />
		<StatTile label="Max Drawdown" value={pct(portfolio.maxDrawdownPct)} sub="limit 15.0%" tone="down" />
	</div>

	<Card eyebrow="Inference Pipeline" title="Decision Flow" tight>
		<div class="pipeline-pad">
			<PipelineFlow stages={status.pipeline} />
		</div>
	</Card>

	<div class="cols two">
		<RegimePanel regime={status.regime} />
		<HealthPanel health={status.health} />
	</div>

	<div class="cols signals">
		<Card eyebrow="RL Policy → Risk Firewall" title="Live Signals">
			{#snippet action()}
				<span class="count mono">{approved} approved</span>
			{/snippet}
			<SignalsTable {signals} />
		</Card>

		<Card eyebrow="Self-Monitoring" title="Event Stream">
			<EventLog events={status.events} />
		</Card>
	</div>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}
	.controls {
		display: flex;
		align-items: center;
		gap: 12px;
		font-size: 12px;
	}
	.live,
	.refresh {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 7px 14px;
		border-radius: var(--radius-pill);
		border: 1px solid var(--border);
		background: var(--surface-2);
		color: var(--text-muted);
		font-size: 12px;
		font-weight: 600;
		transition: all 0.15s ease;
	}
	.live .dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--text-dim);
	}
	.live.on {
		color: var(--ok);
		border-color: rgba(47, 224, 138, 0.3);
		background: var(--long-soft);
	}
	.live.on .dot {
		background: var(--ok);
		box-shadow: 0 0 8px var(--ok);
		animation: pulse 1.6s ease-in-out infinite;
	}
	.refresh:hover:not(:disabled) {
		color: var(--text);
		border-color: var(--border-strong);
	}
	.refresh:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.updated {
		color: var(--text-faint);
	}
	.err {
		color: var(--warn);
	}
	.kpis {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 12px;
	}
	.pipeline-pad {
		padding: 14px 16px 16px;
	}
	.cols {
		display: grid;
		gap: 20px;
	}
	.cols.two {
		grid-template-columns: 1.15fr 1fr;
	}
	.cols.signals {
		grid-template-columns: 1.6fr 1fr;
	}
	.count {
		font-size: 12px;
		color: var(--ok);
		font-weight: 600;
	}
	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}
	@media (max-width: 1080px) {
		.cols.two,
		.cols.signals {
			grid-template-columns: 1fr;
		}
	}
</style>
