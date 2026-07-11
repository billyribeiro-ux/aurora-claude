<script lang="ts">
	import type { PageData } from './$types';
	import type { BacktestResult } from '$lib/types';
	import { browser } from '$app/environment';
	import { pct, pctFrac, num, signed, signedPct, shortDate } from '$lib/format';
	import { TRADABLE } from '$lib/universe';
	import Card from '$lib/components/Card.svelte';
	import StatTile from '$lib/components/StatTile.svelte';
	import Badge from '$lib/components/Badge.svelte';
	import Sparkline from '$lib/components/Sparkline.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let fromOverride = $state<string | null>(null);
	let toOverride = $state<string | null>(null);
	let symbol = $state('ALL');
	let loading = $state(false);
	let errorMsg = $state<string | null>(null);
	let result = $state<BacktestResult | null>(null);

	// Derived-fallback: render the server defaults in SSR (no post-hydration
	// flash) while still allowing user overrides via the inputs.
	const from = $derived(fromOverride ?? data.defaultFrom);
	const to = $derived(toOverride ?? data.defaultTo);
	const rangeValid = $derived(Boolean(from && to && from < to));

	const tradable = [...TRADABLE];
	const equityValues = $derived(result ? result.equityCurve.map((p) => p.equity) : []);

	async function run(): Promise<void> {
		if (!browser || loading) return;
		loading = true;
		errorMsg = null;
		try {
			const params = new URLSearchParams({ from, to });
			if (symbol !== 'ALL') params.set('symbol', symbol);
			const res = await fetch(`/api/backtest?${params.toString()}`);
			if (!res.ok) {
				const e = (await res.json().catch(() => ({ message: `status ${res.status}` }))) as {
					message?: string;
				};
				throw new Error(e.message ?? `status ${res.status}`);
			}
			result = (await res.json()) as BacktestResult;
		} catch (e) {
			errorMsg = e instanceof Error ? e.message : 'backtest failed';
			result = null;
		} finally {
			loading = false;
		}
	}

	function outcomeVariant(o: string): 'ok' | 'critical' | 'warn' | 'neutral' {
		if (o === 'target') return 'ok';
		if (o === 'stop') return 'critical';
		if (o === 'timeout') return 'warn';
		return 'neutral';
	}
	function dirVariant(d: number): 'long' | 'short' | 'neutral' {
		return d > 0 ? 'long' : d < 0 ? 'short' : 'neutral';
	}
</script>

<div class="page">
	<Card eyebrow="Historical replay" title="Backtest the decision engine">
		<p class="lede">
			Pick a window and the console replays the <strong>same</strong> regime → signal → risk-firewall
			engine over each historical day, then simulates each approved trade forward (target / stop /
			20-day timeout). Decisions use only data up to each day — outcomes are measured after. The live
			engine is untouched.
		</p>
		<div class="controls">
			<label>
				<span>From</span>
				<input type="date" value={from} max={to} oninput={(e) => (fromOverride = e.currentTarget.value)} />
			</label>
			<label>
				<span>To</span>
				<input type="date" value={to} min={from} oninput={(e) => (toOverride = e.currentTarget.value)} />
			</label>
			<label>
				<span>Symbol</span>
				<select bind:value={symbol}>
					<option value="ALL">All tradable</option>
					{#each tradable as t (t)}
						<option value={t}>{t}</option>
					{/each}
				</select>
			</label>
			<button class="run" type="button" onclick={run} disabled={loading || !rangeValid}>
				{loading ? 'Running…' : 'Run backtest'}
			</button>
		</div>
		{#if errorMsg}
			<div class="err" role="alert"><span aria-hidden="true">⚠</span> {errorMsg}</div>
		{/if}
	</Card>

	{#if result}
		{@const s = result.summary}
		<div class="kpis">
			<StatTile
				label="Total Return"
				value={signedPct(s.totalReturn * 100)}
				sub="{s.closed} closed trades"
				tone={s.totalReturn >= 0 ? 'up' : 'down'}
			/>
			<StatTile label="Win Rate" value={pctFrac(s.winRate)} sub="{s.wins}/{s.closed} wins" tone="accent" />
			<StatTile label="Trades" value={String(s.entered)} sub="{s.proposals} signals · {s.approved} approved" />
			<StatTile
				label="Avg / Trade"
				value={signedPct(s.avgReturn * 100)}
				sub="expectancy {signedPct(s.expectancy * 100)}"
				tone={s.avgReturn >= 0 ? 'up' : 'down'}
			/>
			<StatTile label="Max Drawdown" value={pct(s.maxDrawdown * 100)} tone="down" />
			<StatTile label="Avg Hold" value="{num(s.avgHoldDays, 1)}d" sub="{s.tradingDays} trading days" />
		</div>

		<Card eyebrow="Compounded · size-weighted · independent trades" title="Equity Curve">
			{#if equityValues.length > 1}
				<div class="equity">
					<Sparkline data={equityValues} width={900} height={140} strokeWidth={2} />
				</div>
				<div class="equity-foot">
					<span>1.00 start</span>
					<span class="mono" class:pos={s.totalReturn >= 0} class:neg={s.totalReturn < 0}>
						{num(1 + s.totalReturn, 3)} end · {signedPct(s.totalReturn * 100)}
					</span>
				</div>
			{:else}
				<p class="muted">Not enough closed trades to plot an equity curve.</p>
			{/if}
		</Card>

		<Card eyebrow="Decision ledger" title="Signals">
			{#snippet action()}
				<span class="meta mono">
					{result?.symbolFilter ?? 'universe'} · {result?.dataSource}{result?.truncated
						? ' · showing latest 750'
						: ''}
				</span>
			{/snippet}
			{#if result.signals.length === 0}
				<p class="muted">No directional signals were generated in this window.</p>
			{:else}
				<div class="table-wrap">
					<table>
						<thead>
							<tr>
								<th class="l">Date</th>
								<th class="l">Symbol</th>
								<th>Bias</th>
								<th class="r">Score</th>
								<th class="r">Conf.</th>
								<th class="r">Size</th>
								<th class="r">Stop</th>
								<th class="r">Target</th>
								<th class="r">Hold</th>
								<th>Outcome</th>
								<th class="r">Return</th>
							</tr>
						</thead>
						<tbody>
							{#each result.signals as sig, i (sig.date + sig.symbol + i)}
								<tr>
									<td class="l mono">{shortDate(sig.date)}</td>
									<td class="l mono sym">{sig.symbol}</td>
									<td><Badge variant={dirVariant(sig.direction)}>{sig.direction > 0 ? 'LONG' : 'SHORT'}</Badge></td>
									<td class="r mono">{signed(sig.score, 2)}</td>
									<td class="r mono">{pctFrac(sig.confidence)}</td>
									<td class="r mono">{pctFrac(sig.positionSize)}</td>
									<td class="r mono">{pctFrac(sig.stopDistance)}</td>
									<td class="r mono">{pctFrac(sig.targetDistance)}</td>
									<td class="r mono">{sig.outcome === 'open' ? '—' : `${sig.holdDays}d`}</td>
									<td><Badge variant={outcomeVariant(sig.outcome)}>{sig.outcome.toUpperCase()}</Badge></td>
									<td
										class="r mono"
										class:pos={sig.realizedReturn > 0}
										class:neg={sig.realizedReturn < 0}
									>
										{sig.outcome === 'open' ? '—' : signedPct(sig.realizedReturn * 100)}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</Card>
	{:else if loading}
		<div class="empty" aria-busy="true">Running backtest…</div>
	{:else}
		<div class="empty">Pick a date range and run a backtest to see the signals the engine produces.</div>
	{/if}
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}
	.lede {
		margin: 0 0 16px;
		color: var(--text-muted);
		line-height: 1.6;
		font-size: 13.5px;
		max-width: 92ch;
	}
	.lede strong {
		color: var(--text);
	}
	.controls {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		gap: 14px;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 5px;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dim);
	}
	input,
	select {
		font-family: inherit;
		font-size: 13px;
		color: var(--text);
		background: var(--surface-2);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 8px 10px;
		min-width: 150px;
		color-scheme: dark light;
	}
	input:focus,
	select:focus {
		border-color: var(--accent);
		outline: none;
	}
	.run {
		padding: 9px 20px;
		border-radius: var(--radius-sm);
		border: 1px solid var(--accent-line);
		background: var(--accent-soft);
		color: var(--accent);
		font-weight: 600;
		font-size: 13px;
		transition: all 0.15s ease;
	}
	.run:hover:not(:disabled) {
		background: color-mix(in srgb, var(--accent-soft) 60%, var(--accent) 12%);
	}
	.run:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.err {
		margin-top: 14px;
		color: var(--critical);
		background: var(--short-soft);
		border: 1px solid rgba(255, 95, 115, 0.25);
		border-radius: var(--radius-sm);
		padding: 8px 12px;
		font-size: 13px;
	}
	.kpis {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
		gap: 12px;
	}
	.equity {
		width: 100%;
	}
	.equity-foot {
		display: flex;
		justify-content: space-between;
		margin-top: 8px;
		font-size: 12px;
		color: var(--text-dim);
	}
	.meta {
		font-size: 11px;
		color: var(--text-faint);
	}
	.muted {
		color: var(--text-dim);
		font-size: 13px;
		margin: 0;
	}
	.table-wrap {
		overflow-x: auto;
		max-height: 620px;
		overflow-y: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 12.5px;
	}
	thead th {
		position: sticky;
		top: 0;
		background: var(--surface);
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dim);
		padding: 0 10px 10px;
		text-align: right;
		white-space: nowrap;
		border-bottom: 1px solid var(--border);
	}
	th.l {
		text-align: left;
	}
	td {
		padding: 8px 10px;
		text-align: right;
		white-space: nowrap;
		border-bottom: 1px solid var(--border);
	}
	td.l {
		text-align: left;
	}
	.sym {
		font-weight: 700;
	}
	.pos {
		color: var(--up);
	}
	.neg {
		color: var(--down);
	}
	.empty {
		padding: 48px;
		text-align: center;
		color: var(--text-faint);
		background: var(--surface);
		border: 1px dashed var(--border-strong);
		border-radius: var(--radius-lg);
		font-size: 14px;
	}
	@media (max-width: 620px) {
		input,
		select {
			min-width: 120px;
		}
	}
</style>
