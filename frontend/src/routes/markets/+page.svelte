<script lang="ts">
	import type { PageServerData } from './$types';
	import type { Candle } from '$lib/types';
	import Card from '$lib/components/Card.svelte';
	import PriceChart from '$lib/components/PriceChart.svelte';
	import Watchlist from '$lib/components/Watchlist.svelte';

	interface Props {
		data: PageServerData;
	}

	let { data }: Props = $props();

	// User-selected override falls back to the server-provided defaults.
	let selectedSymbol = $state<string | null>(null);
	let fetched = $state<{ name: string; candles: Candle[] } | null>(null);
	let loading = $state(false);

	const quotes = $derived(data.snapshot.quotes);
	const selected = $derived(selectedSymbol ?? data.initialSymbol);
	const selectedName = $derived(fetched?.name ?? data.initialName);
	const candles = $derived(fetched?.candles ?? data.initialCandles);

	async function selectSymbol(symbol: string): Promise<void> {
		if (symbol === selected && candles.length > 1) return;
		selectedSymbol = symbol;
		loading = true;
		try {
			const res = await fetch(`/api/history?symbol=${encodeURIComponent(symbol)}&days=120`);
			if (!res.ok) throw new Error(`status ${res.status}`);
			fetched = (await res.json()) as { name: string; candles: Candle[] };
		} catch {
			fetched = { name: symbol, candles: [] };
		} finally {
			loading = false;
		}
	}
</script>

<div class="page">
	<div class="grid">
		<Card eyebrow="Universe" title="Watchlist" tight>
			<div class="watch-scroll">
				<Watchlist {quotes} {selected} onselect={selectSymbol} />
			</div>
		</Card>

		<div class="right">
			<PriceChart {candles} symbol={selected} name={selectedName} {loading} />
			<Card eyebrow="Context" title="Why it matters">
				<p class="note">
					The live engine reads this same price action across the full universe — market ETFs, macro
					instruments and sectors — to detect the regime and score signals. In the target design, a
					foundation encoder consumes it to build a latent market state; that trained stack is not
					yet live. Selecting a symbol previews the raw series feeding the engine.
				</p>
			</Card>
		</div>
	</div>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}
	.grid {
		display: grid;
		grid-template-columns: 320px 1fr;
		gap: 20px;
		align-items: start;
	}
	.watch-scroll {
		max-height: 620px;
		overflow-y: auto;
	}
	.right {
		display: flex;
		flex-direction: column;
		gap: 20px;
		min-width: 0;
	}
	.note {
		margin: 0;
		color: var(--text-muted);
		line-height: 1.6;
		font-size: 13.5px;
		max-width: 72ch;
	}
	@media (max-width: 900px) {
		.grid {
			grid-template-columns: 1fr;
		}
		.watch-scroll {
			max-height: 360px;
		}
	}
</style>
