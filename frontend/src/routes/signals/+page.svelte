<script lang="ts">
	import type { PageServerData } from './$types';
	import { pctFrac } from '$lib/format';
	import Card from '$lib/components/Card.svelte';
	import StatTile from '$lib/components/StatTile.svelte';
	import SignalsTable from '$lib/components/SignalsTable.svelte';

	interface Props {
		data: PageServerData;
	}

	let { data }: Props = $props();

	const signals = $derived(data.snapshot.signals);
	const approved = $derived(signals.filter((s) => s.approved));
	const directional = $derived(signals.filter((s) => s.direction !== 0));
	const avgConf = $derived(
		signals.length ? signals.reduce((a, s) => a + s.confidence, 0) / signals.length : 0
	);
	const deployed = $derived(approved.reduce((a, s) => a + s.positionSize, 0));

	const firewallRules = [
		'Reject any proposal whose calibrated confidence sits below the 48% floor.',
		'Stand aside when annualized volatility exceeds the 95% ceiling.',
		'Block all new entries in a CRISIS regime; suppress new longs in a BEAR trend.',
		'Trim or reject positions that would breach the 10% portfolio-heat budget.',
		'Drop positions sized below the 2% minimum — not worth the friction.'
	];
</script>

<div class="page">
	<div class="kpis">
		<StatTile label="Proposals" value={String(signals.length)} sub="from RL policy" />
		<StatTile label="Approved" value={String(approved.length)} sub="cleared firewall" tone="up" />
		<StatTile
			label="Blocked"
			value={String(directional.length - approved.length)}
			sub="directional, rejected"
			tone="down"
		/>
		<StatTile label="Avg Confidence" value={pctFrac(avgConf)} tone="accent" />
		<StatTile label="Deployed Exposure" value={pctFrac(deployed)} sub="of risk budget" />
	</div>

	<Card eyebrow="Decision Ledger" title="All Signals">
		{#snippet action()}
			<span class="hint">click a row for the decision trail</span>
		{/snippet}
		<SignalsTable {signals} />
	</Card>

	<Card eyebrow="How decisions clear" title="Risk Firewall Policy">
		<p class="lede">
			The neural pipeline never trades directly. Every RL proposal must pass an independent risk
			firewall before it becomes an approved signal:
		</p>
		<ul class="rules">
			{#each firewallRules as rule, i (i)}
				<li><span class="n mono">{i + 1}</span>{rule}</li>
			{/each}
		</ul>
	</Card>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}
	.kpis {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 12px;
	}
	.hint {
		font-size: 11px;
		color: var(--text-faint);
	}
	.lede {
		margin: 0 0 14px;
		color: var(--text-muted);
		line-height: 1.6;
		font-size: 13.5px;
		max-width: 70ch;
	}
	.rules {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.rules li {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		font-size: 13px;
		color: var(--text-muted);
		line-height: 1.5;
	}
	.n {
		display: grid;
		place-items: center;
		flex-shrink: 0;
		width: 22px;
		height: 22px;
		border-radius: 6px;
		background: var(--accent-soft);
		color: var(--accent);
		font-size: 11px;
		font-weight: 700;
	}
</style>
