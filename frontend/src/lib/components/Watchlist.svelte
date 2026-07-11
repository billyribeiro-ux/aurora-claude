<script lang="ts">
	import Sparkline from './Sparkline.svelte';
	import Delta from './Delta.svelte';
	import type { Quote } from '$lib/types';
	import type { UniverseGroup } from '$lib/universe';
	import { groupOf } from '$lib/universe';
	import { num } from '$lib/format';

	interface Props {
		quotes: Quote[];
		selected?: string;
		onselect?: (symbol: string) => void;
	}

	let { quotes, selected, onselect }: Props = $props();

	const GROUP_LABEL: Record<UniverseGroup, string> = {
		market: 'Market',
		macro: 'Macro',
		sector: 'Sectors',
		equity: 'Equities'
	};
	const ORDER: UniverseGroup[] = ['market', 'macro', 'sector', 'equity'];

	const grouped = $derived.by(() => {
		const buckets: Record<UniverseGroup, Quote[]> = {
			market: [],
			macro: [],
			sector: [],
			equity: []
		};
		for (const q of quotes) {
			buckets[groupOf(q.symbol)].push(q);
		}
		return ORDER.filter((g) => buckets[g].length > 0).map((g) => ({
			group: g,
			quotes: buckets[g]
		}));
	});
</script>

<div class="watchlist">
	{#each grouped as section (section.group)}
		<div class="group">
			<div class="group-head">{GROUP_LABEL[section.group]}</div>
			{#each section.quotes as q (q.symbol)}
				<button
					type="button"
					class="quote"
					class:selected={selected === q.symbol}
					onclick={() => onselect?.(q.symbol)}
				>
					<div class="ident">
						<span class="sym mono">{q.symbol}</span>
						<span class="name">{q.name}</span>
					</div>
					<div class="spark">
						<Sparkline data={q.spark} width={72} height={26} />
					</div>
					<div class="figures">
						<span class="price mono">{num(q.price, 2)}</span>
						<Delta value={q.changePercent} size="sm" showArrow={false} />
					</div>
				</button>
			{/each}
		</div>
	{/each}
</div>

<style>
	.watchlist {
		display: flex;
		flex-direction: column;
	}
	.group-head {
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--text-dim);
		padding: 12px 16px 6px;
		position: sticky;
		top: 0;
		background: var(--surface);
		z-index: 1;
	}
	.quote {
		display: grid;
		grid-template-columns: 1fr auto auto;
		align-items: center;
		gap: 12px;
		width: 100%;
		padding: 9px 16px;
		background: transparent;
		border: none;
		border-left: 2px solid transparent;
		text-align: left;
		color: inherit;
		transition: background 0.12s ease;
	}
	.quote:hover {
		background: var(--surface-2);
	}
	.quote.selected {
		background: var(--surface-2);
		border-left-color: var(--accent);
	}
	.ident {
		display: flex;
		flex-direction: column;
		gap: 1px;
		min-width: 0;
	}
	.sym {
		font-weight: 700;
		font-size: 13px;
	}
	.name {
		font-size: 11px;
		color: var(--text-dim);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.spark {
		opacity: 0.85;
	}
	.figures {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}
	.price {
		font-size: 13px;
		font-weight: 600;
	}
</style>
