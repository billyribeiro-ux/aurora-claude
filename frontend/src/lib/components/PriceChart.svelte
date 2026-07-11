<script lang="ts">
	import Delta from './Delta.svelte';
	import type { Candle } from '$lib/types';
	import { num, shortDate } from '$lib/format';

	interface Props {
		candles: Candle[];
		symbol: string;
		name?: string;
		loading?: boolean;
	}

	let { candles, symbol, name, loading = false }: Props = $props();

	const W = 760;
	const H = 280;
	const PAD_TOP = 18;
	const PAD_BOTTOM = 26;

	interface Geo {
		line: string;
		area: string;
		pts: { x: number; y: number }[];
		min: number;
		max: number;
		mid: number;
		up: boolean;
	}

	const geo = $derived.by<Geo>(() => {
		const n = candles.length;
		if (n < 2) return { line: '', area: '', pts: [], min: 0, max: 0, mid: 0, up: true };
		let min = Math.min(...candles.map((c) => c.low));
		let max = Math.max(...candles.map((c) => c.high));
		const pad = (max - min) * 0.08 || 1;
		min -= pad;
		max += pad;
		const span = max - min || 1;
		const plotH = H - PAD_TOP - PAD_BOTTOM;
		const stepX = W / (n - 1);
		const pts = candles.map((c, i) => ({
			x: i * stepX,
			y: PAD_TOP + plotH - ((c.close - min) / span) * plotH
		}));
		const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
		const area = `${line} L${W},${H - PAD_BOTTOM} L0,${H - PAD_BOTTOM} Z`;
		return { line, area, pts, min, max, mid: (min + max) / 2, up: candles[n - 1].close >= candles[0].close };
	});

	let hover = $state<number | null>(null);
	const hoverCandle = $derived(hover !== null ? candles[hover] : null);
	const hoverPt = $derived(hover !== null ? geo.pts[hover] : null);

	function onmove(e: PointerEvent): void {
		if (candles.length < 2) return;
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		const frac = (e.clientX - rect.left) / rect.width;
		hover = Math.max(0, Math.min(candles.length - 1, Math.round(frac * (candles.length - 1))));
	}

	const color = $derived(geo.up ? 'var(--up)' : 'var(--down)');
	const first = $derived(candles.length ? candles[0] : null);
	const last = $derived(candles.length ? candles[candles.length - 1] : null);
	const changePct = $derived(
		first && last && first.close ? ((last.close - first.close) / first.close) * 100 : 0
	);
	const tooltipLeft = $derived(
		hover !== null && candles.length > 1 ? (hover / (candles.length - 1)) * 100 : 0
	);
</script>

<div class="chart-card">
	<header class="head">
		<div class="ident">
			<h3 class="mono">{symbol}</h3>
			{#if name}<span class="name">{name}</span>{/if}
		</div>
		{#if last}
			<div class="quote">
				<span class="last mono">{num(last.close, 2)}</span>
				<Delta value={changePct} />
				<span class="range-note">{candles.length}d</span>
			</div>
		{/if}
	</header>

	<div class="plot" class:loading>
		{#if candles.length < 2}
			<div class="placeholder">{loading ? 'Loading price history…' : 'No data available'}</div>
		{:else}
			<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" role="img" aria-label="{symbol} price history">
				<line x1="0" y1={PAD_TOP} x2={W} y2={PAD_TOP} class="grid" />
				<line x1="0" y1={H / 2} x2={W} y2={H / 2} class="grid" />
				<line x1="0" y1={H - PAD_BOTTOM} x2={W} y2={H - PAD_BOTTOM} class="grid" />
				<path d={geo.area} fill={color} fill-opacity="0.1" />
				<path
					d={geo.line}
					fill="none"
					stroke={color}
					stroke-width="2"
					stroke-linejoin="round"
					vector-effect="non-scaling-stroke"
				/>
				{#if hoverPt}
					<line x1={hoverPt.x} y1={PAD_TOP} x2={hoverPt.x} y2={H - PAD_BOTTOM} class="crosshair" />
					<circle cx={hoverPt.x} cy={hoverPt.y} r="4" fill={color} stroke="var(--surface)" stroke-width="2" vector-effect="non-scaling-stroke" />
				{/if}
			</svg>

			<div class="y-labels">
				<span class="mono">{num(geo.max, 2)}</span>
				<span class="mono">{num(geo.mid, 2)}</span>
				<span class="mono">{num(geo.min, 2)}</span>
			</div>

			<div class="x-labels">
				<span>{first ? shortDate(first.date) : ''}</span>
				<span>{last ? shortDate(last.date) : ''}</span>
			</div>

			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="overlay" onpointermove={onmove} onpointerleave={() => (hover = null)}></div>

			{#if hoverCandle}
				<div class="tooltip" style:left="{tooltipLeft}%" class:flip={tooltipLeft > 60}>
					<div class="tt-date">{shortDate(hoverCandle.date)}</div>
					<div class="tt-row"><span>O</span><span class="mono">{num(hoverCandle.open, 2)}</span></div>
					<div class="tt-row"><span>H</span><span class="mono">{num(hoverCandle.high, 2)}</span></div>
					<div class="tt-row"><span>L</span><span class="mono">{num(hoverCandle.low, 2)}</span></div>
					<div class="tt-row strong"><span>C</span><span class="mono">{num(hoverCandle.close, 2)}</span></div>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.chart-card {
		display: flex;
		flex-direction: column;
		gap: 12px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		padding: 16px 18px 18px;
	}
	.head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
	}
	.ident {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	h3 {
		font-size: 18px;
		font-weight: 700;
	}
	.name {
		font-size: 12px;
		color: var(--text-dim);
	}
	.quote {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.last {
		font-size: 18px;
		font-weight: 700;
	}
	.range-note {
		font-size: 11px;
		color: var(--text-faint);
		padding: 2px 6px;
		border: 1px solid var(--border);
		border-radius: var(--radius-pill);
	}
	.plot {
		position: relative;
		width: 100%;
		aspect-ratio: 760 / 280;
	}
	svg {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}
	.grid {
		stroke: var(--border);
		stroke-width: 1;
		stroke-dasharray: 3 5;
		vector-effect: non-scaling-stroke;
	}
	.crosshair {
		stroke: var(--text-dim);
		stroke-width: 1;
		stroke-dasharray: 2 3;
		vector-effect: non-scaling-stroke;
	}
	.overlay {
		position: absolute;
		inset: 0;
		cursor: crosshair;
	}
	.y-labels {
		position: absolute;
		top: 10px;
		bottom: 20px;
		right: 4px;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: flex-end;
		font-size: 10px;
		color: var(--text-faint);
		pointer-events: none;
	}
	.x-labels {
		position: absolute;
		left: 2px;
		right: 2px;
		bottom: 2px;
		display: flex;
		justify-content: space-between;
		font-size: 10px;
		color: var(--text-faint);
		pointer-events: none;
	}
	.tooltip {
		position: absolute;
		top: 8px;
		transform: translateX(-50%);
		background: var(--elevated);
		border: 1px solid var(--border-strong);
		border-radius: var(--radius-sm);
		padding: 8px 10px;
		font-size: 11px;
		box-shadow: var(--shadow);
		pointer-events: none;
		min-width: 84px;
	}
	.tooltip.flip {
		transform: translateX(-100%);
	}
	.tt-date {
		font-weight: 600;
		margin-bottom: 4px;
		color: var(--text);
	}
	.tt-row {
		display: flex;
		justify-content: space-between;
		gap: 14px;
		color: var(--text-muted);
	}
	.tt-row.strong {
		color: var(--text);
		font-weight: 600;
	}
	.placeholder {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-faint);
		font-size: 13px;
	}
</style>
