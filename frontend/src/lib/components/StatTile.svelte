<script lang="ts">
	import Delta from './Delta.svelte';
	import Sparkline from './Sparkline.svelte';

	interface Props {
		label: string;
		value: string;
		sub?: string;
		delta?: number;
		tone?: 'default' | 'up' | 'down' | 'accent';
		spark?: number[];
	}

	let { label, value, sub, delta, tone = 'default', spark }: Props = $props();
</script>

<div class="tile {tone}">
	<span class="label">{label}</span>
	<span class="value mono">{value}</span>
	<div class="foot">
		{#if delta !== undefined}
			<Delta value={delta} size="sm" />
		{/if}
		{#if sub}<span class="sub">{sub}</span>{/if}
	</div>
	{#if spark && spark.length > 1}
		<div class="spark">
			<Sparkline data={spark} width={140} height={30} />
		</div>
	{/if}
</div>

<style>
	.tile {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: 16px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		overflow: hidden;
		min-width: 0;
	}
	.tile::before {
		content: '';
		position: absolute;
		inset: 0 auto 0 0;
		width: 3px;
		background: var(--border-strong);
	}
	.tile.up::before {
		background: var(--up);
	}
	.tile.down::before {
		background: var(--down);
	}
	.tile.accent::before {
		background: var(--aurora-gradient);
	}
	.label {
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--text-dim);
	}
	.value {
		font-size: 24px;
		font-weight: 700;
		letter-spacing: -0.02em;
		line-height: 1.1;
	}
	.foot {
		display: flex;
		align-items: center;
		gap: 8px;
		min-height: 16px;
	}
	.sub {
		font-size: 12px;
		color: var(--text-muted);
	}
	.spark {
		margin-top: 4px;
		opacity: 0.9;
	}
</style>
