<script lang="ts">
	import type { PageServerData } from './$types';
	import Card from '$lib/components/Card.svelte';
	import HealthPanel from '$lib/components/HealthPanel.svelte';
	import PipelineFlow from '$lib/components/PipelineFlow.svelte';
	import EventLog from '$lib/components/EventLog.svelte';
	import Disclosure from '$lib/components/Disclosure.svelte';

	interface Props {
		data: PageServerData;
	}

	let { data }: Props = $props();

	const status = $derived(data.snapshot.status);

	const loop = [
		{ step: 'New Data', detail: 'Fresh market data streams into the experience database.' },
		{ step: 'Performance Analysis', detail: 'Rolling reward, hit-rate and calibration are measured.' },
		{ step: 'Drift Detection', detail: 'Latent and reward drift are tested against baselines.' },
		{
			step: 'Statistical Gate',
			detail: 'Is the change statistically justified? If not — continue unchanged.'
		},
		{ step: 'Fine-Tune', detail: 'Controlled adaptation on the new experience.' },
		{ step: 'Validate', detail: 'Walk-forward + Monte-Carlo before anything ships.' },
		{ step: 'Deploy', detail: 'A new version is promoted only after it clears validation.' }
	];
</script>

<div class="page">
	<Disclosure kind="design" />

	<div class="cols">
		<HealthPanel health={status.health} />

		<Card eyebrow="Pipeline" title="Live Stage Latency" tight>
			<div class="pad">
				<PipelineFlow stages={status.pipeline} />
			</div>
		</Card>
	</div>

	<Card eyebrow="Continual Learning" title="Weekly Improvement Loop">
		<p class="lede">
			Adaptation is controlled — a system that changes constantly becomes unstable. Each week the
			monitor runs this loop, and nothing ships unless the change is statistically justified and
			clears validation.
		</p>
		<ol class="loop">
			{#each loop as node, i (i)}
				<li>
					<span class="idx mono">{String(i + 1).padStart(2, '0')}</span>
					<div class="body">
						<span class="step">{node.step}</span>
						<span class="detail">{node.detail}</span>
					</div>
				</li>
			{/each}
		</ol>
	</Card>

	<Card eyebrow="Self-Monitoring" title="Event Stream">
		<EventLog events={status.events} max={20} />
	</Card>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}
	.cols {
		display: grid;
		grid-template-columns: 1fr 1.2fr;
		gap: 20px;
		align-items: start;
	}
	.pad {
		padding: 14px 16px 16px;
	}
	.lede {
		margin: 0 0 16px;
		color: var(--text-muted);
		line-height: 1.6;
		font-size: 13.5px;
		max-width: 74ch;
	}
	.loop {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 12px;
	}
	.loop li {
		display: flex;
		gap: 12px;
		padding: 14px;
		background: var(--surface-2);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}
	.idx {
		color: var(--accent);
		font-weight: 700;
		font-size: 13px;
	}
	.body {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.step {
		font-weight: 600;
		font-size: 13px;
	}
	.detail {
		font-size: 12px;
		color: var(--text-dim);
		line-height: 1.5;
	}
	@media (max-width: 900px) {
		.cols {
			grid-template-columns: 1fr;
		}
	}
</style>
