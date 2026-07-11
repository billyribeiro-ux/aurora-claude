<script lang="ts">
	import Badge from './Badge.svelte';
	import type { TradingSignal } from '$lib/types';
	import { pctFrac, num, signed } from '$lib/format';

	interface Props {
		signals: TradingSignal[];
		onselect?: (symbol: string) => void;
	}

	let { signals, onselect }: Props = $props();

	let expanded = $state<string | null>(null);

	function toggle(symbol: string): void {
		expanded = expanded === symbol ? null : symbol;
		onselect?.(symbol);
	}

	function dirVariant(direction: number): 'long' | 'short' | 'neutral' {
		if (direction > 0) return 'long';
		if (direction < 0) return 'short';
		return 'neutral';
	}

	function dirLabel(direction: number): string {
		if (direction > 0) return 'LONG';
		if (direction < 0) return 'SHORT';
		return 'FLAT';
	}
</script>

<div class="wrap">
	<table>
		<thead>
			<tr>
				<th class="l">Symbol</th>
				<th>Bias</th>
				<th class="r">Score</th>
				<th class="r">Conf.</th>
				<th class="r">Size</th>
				<th class="r">Stop</th>
				<th class="r">Target</th>
				<th class="r">R:R</th>
				<th class="r">Decision</th>
			</tr>
		</thead>
		<tbody>
			{#each signals as s (s.symbol)}
				<tr
					class="row"
					class:open={expanded === s.symbol}
					class:muted={!s.approved}
					onclick={() => toggle(s.symbol)}
				>
					<td class="l">
						<span class="sym mono">{s.symbol}</span>
					</td>
					<td>
						<Badge variant={dirVariant(s.direction)}>{dirLabel(s.direction)}</Badge>
					</td>
					<td class="r mono" class:pos={s.score > 0} class:neg={s.score < 0}>{signed(s.score, 2)}</td>
					<td class="r">
						<div class="conf">
							<span class="mono">{pctFrac(s.confidence)}</span>
							<span class="cbar"><span class="cfill" style:width="{s.confidence * 100}%"></span></span>
						</div>
					</td>
					<td class="r mono">{s.direction === 0 ? '—' : pctFrac(s.positionSize)}</td>
					<td class="r mono">{pctFrac(s.stopDistance)}</td>
					<td class="r mono">{pctFrac(s.targetDistance)}</td>
					<td class="r mono">{num(s.expectedReward, 1)}</td>
					<td class="r">
						<Badge variant={s.approved ? 'ok' : 'neutral'} dot>
							{s.approved ? 'APPROVED' : 'BLOCKED'}
						</Badge>
					</td>
				</tr>
				{#if expanded === s.symbol}
					<tr class="detail-row">
						<td colspan="9">
							<div class="rationale">
								<span class="eyebrow">Decision trail · {s.regime.replace('_', ' ')}</span>
								<ul>
									{#each s.rationale as reason, i (i)}
										<li>{reason}</li>
									{/each}
								</ul>
							</div>
						</td>
					</tr>
				{/if}
			{/each}
			{#if signals.length === 0}
				<tr><td colspan="9" class="empty">No signals generated.</td></tr>
			{/if}
		</tbody>
	</table>
</div>

<style>
	.wrap {
		overflow-x: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
	}
	thead th {
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--text-dim);
		padding: 0 12px 10px;
		text-align: right;
		white-space: nowrap;
		border-bottom: 1px solid var(--border);
	}
	th.l {
		text-align: left;
	}
	td {
		padding: 10px 12px;
		text-align: right;
		white-space: nowrap;
		border-bottom: 1px solid var(--border);
	}
	td.l {
		text-align: left;
	}
	.row {
		cursor: pointer;
		transition: background 0.15s ease;
	}
	.row:hover {
		background: var(--surface-2);
	}
	.row.open {
		background: var(--surface-2);
	}
	.row.muted td:not(.l) {
		color: var(--text-dim);
	}
	.sym {
		font-weight: 700;
		font-size: 13px;
	}
	.pos {
		color: var(--up);
	}
	.neg {
		color: var(--down);
	}
	.conf {
		display: inline-flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 4px;
	}
	.cbar {
		width: 54px;
		height: 4px;
		border-radius: 999px;
		background: var(--surface-3);
		overflow: hidden;
	}
	.cfill {
		display: block;
		height: 100%;
		background: var(--aurora-gradient);
	}
	.detail-row td {
		background: var(--surface-2);
		padding: 0 12px 14px;
	}
	.rationale {
		display: flex;
		flex-direction: column;
		gap: 8px;
		text-align: left;
		padding-top: 4px;
	}
	.rationale ul {
		margin: 0;
		padding-left: 18px;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.rationale li {
		color: var(--text-muted);
		font-size: 12.5px;
		line-height: 1.5;
	}
	.empty {
		text-align: center;
		color: var(--text-faint);
		padding: 24px;
	}
</style>
