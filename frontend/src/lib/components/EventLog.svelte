<script lang="ts">
	import type { EventEntry } from '$lib/types';
	import { clock } from '$lib/format';

	interface Props {
		events: EventEntry[];
		max?: number;
	}

	let { events, max = 12 }: Props = $props();

	const shown = $derived(events.slice(0, max));
</script>

<ul class="log">
	{#each shown as event, i (event.time + i)}
		<li class="entry {event.level}">
			<span class="time mono">{clock(event.time)}</span>
			<span class="rail" aria-hidden="true"></span>
			<span class="msg">{event.message}</span>
		</li>
	{/each}
	{#if shown.length === 0}
		<li class="empty">No events recorded.</li>
	{/if}
</ul>

<style>
	.log {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
	}
	.entry {
		display: grid;
		grid-template-columns: 64px 14px 1fr;
		align-items: start;
		gap: 8px;
		padding: 9px 0;
		font-size: 12.5px;
		border-bottom: 1px solid var(--border);
	}
	.entry:last-child {
		border-bottom: none;
	}
	.time {
		color: var(--text-faint);
		font-size: 11px;
		padding-top: 1px;
	}
	.rail {
		position: relative;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		margin-top: 4px;
		background: var(--text-dim);
	}
	.msg {
		color: var(--text-muted);
		line-height: 1.5;
	}
	.info .rail {
		background: var(--info);
	}
	.success .rail {
		background: var(--ok);
	}
	.warn .rail {
		background: var(--warn);
	}
	.critical .rail {
		background: var(--critical);
	}
	.critical .msg {
		color: var(--text);
	}
	.empty {
		color: var(--text-faint);
		font-size: 12px;
		padding: 8px 0;
	}
</style>
