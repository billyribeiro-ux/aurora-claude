<script lang="ts">
	import type { PipelineStage } from '$lib/types';

	interface Props {
		stages: PipelineStage[];
	}

	let { stages }: Props = $props();
</script>

<div class="flow" role="list" aria-label="Inference pipeline">
	{#each stages as stage, i (stage.key)}
		<div class="stage {stage.status}" role="listitem">
			<div class="node">
				<span class="dot"></span>
				<span class="label">{stage.label}</span>
			</div>
			<span class="detail mono">{stage.detail}</span>
			{#if stage.latencyMs > 0}
				<span class="latency mono">{stage.latencyMs}ms</span>
			{/if}
		</div>
		{#if i < stages.length - 1}
			<span class="arrow" aria-hidden="true">→</span>
		{/if}
	{/each}
</div>

<style>
	.flow {
		display: flex;
		align-items: stretch;
		gap: 4px;
		overflow-x: auto;
		padding: 4px 2px;
	}
	.stage {
		display: flex;
		flex-direction: column;
		gap: 6px;
		flex: 1 1 0;
		min-width: 132px;
		padding: 12px 14px;
		border-radius: var(--radius);
		background: var(--surface-2);
		border: 1px solid var(--border);
	}
	.node {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--text-dim);
		flex-shrink: 0;
	}
	.label {
		font-size: 12px;
		font-weight: 600;
		white-space: nowrap;
	}
	.detail {
		font-size: 11px;
		color: var(--text-muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.latency {
		font-size: 10px;
		color: var(--text-faint);
	}
	.arrow {
		align-self: center;
		color: var(--text-faint);
		font-size: 14px;
		flex-shrink: 0;
	}
	.stage.ok .dot {
		background: var(--ok);
		box-shadow: 0 0 8px rgba(47, 224, 138, 0.5);
	}
	.stage.active {
		border-color: var(--accent-line);
	}
	.stage.active .dot {
		background: var(--accent);
		box-shadow: 0 0 10px rgba(53, 230, 195, 0.6);
		animation: blink 1.6s ease-in-out infinite;
	}
	.stage.warn {
		border-color: rgba(255, 176, 32, 0.35);
	}
	.stage.warn .dot {
		background: var(--warn);
		box-shadow: 0 0 8px rgba(255, 176, 32, 0.5);
	}
	.stage.idle {
		opacity: 0.6;
	}
	@keyframes blink {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.4;
		}
	}
</style>
