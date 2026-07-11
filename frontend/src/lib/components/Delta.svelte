<script lang="ts">
	import { signedPct } from '$lib/format';

	interface Props {
		/** An already-percentage change value, e.g. 1.5 for +1.50%. */
		value: number;
		digits?: number;
		showArrow?: boolean;
		size?: 'sm' | 'md';
	}

	let { value, digits = 2, showArrow = true, size = 'md' }: Props = $props();

	const dir = $derived(value > 0 ? 'up' : value < 0 ? 'down' : 'flat');
	const arrow = $derived(value > 0 ? '▲' : value < 0 ? '▼' : '■');
</script>

<span class="delta {dir} {size}">
	{#if showArrow}<span class="arrow">{arrow}</span>{/if}
	<span class="mono">{signedPct(value, digits)}</span>
</span>

<style>
	.delta {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-weight: 600;
		white-space: nowrap;
	}
	.sm {
		font-size: 12px;
	}
	.arrow {
		font-size: 0.7em;
		line-height: 1;
	}
	.up {
		color: var(--up);
	}
	.down {
		color: var(--down);
	}
	.flat {
		color: var(--flat);
	}
</style>
