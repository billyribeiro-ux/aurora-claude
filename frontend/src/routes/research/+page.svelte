<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import Badge from '$lib/components/Badge.svelte';
	import Disclosure from '$lib/components/Disclosure.svelte';
	import StatTile from '$lib/components/StatTile.svelte';

	// Final research findings from the certification harness (Modules 12–15).
	// Static by design: these are measured results, not live metrics.
	const evaluations = [
		{ name: 'Survivor-only universe', detail: 'biased — only names that survived to 2026', sharpe: '+1.28', tone: 'down' as const, note: 'a mirage' },
		{ name: 'Survivorship-free (point-in-time)', detail: 'includes 197 removed / delisted names', sharpe: '−0.88', tone: 'down' as const, note: 'the bias was the edge' },
		{ name: '+ rich features, rank-normalized', detail: '24 leakage-safe factors', sharpe: '−0.16', tone: 'down' as const, note: 'method helped; still no edge' },
		{ name: '+ leakage-safe fundamentals', detail: 'point-in-time value/quality', sharpe: '−0.57', tone: 'down' as const, note: 'hurt in this regime' },
		{ name: 'Baseline: buy-and-hold SPY', detail: 'the bar none of the above beat', sharpe: '+1.32', tone: 'up' as const, note: 'reference' }
	];

	const proven = [
		{ label: 'Live data vs raw source', value: '120/120', sub: 'exact OHLC match' },
		{ label: 'No look-ahead leakage', value: 'verified', sub: 'feature + label embargo' },
		{ label: 'Encoder vs random', value: '+64%', sub: 'masked reconstruction' },
		{ label: 'Test coverage', value: '47 + 12', sub: 'python + e2e, passing' }
	];

	const methodology = [
		['Survivorship-free', 'Point-in-time S&P 500 membership including the companies that died.'],
		['PBO (CSCV)', 'Bailey & López de Prado — measures backtest-overfitting probability directly.'],
		['Embargoed walk-forward', 'No training label may touch the test period.'],
		['Leakage-safe fundamentals', 'Data usable only after its filing date (+90-day conservative lag).'],
		['Reported as-measured', 'The console labels what is heuristic, trained, or without demonstrated edge.']
	];
</script>

<div class="page">
	<Disclosure kind="design" />

	<Card eyebrow="Evidence Ledger" title="What the hard evidence actually says">
		<p class="lede">
			AURORA is built to one standard: <strong>hard evidence</strong>. It makes <strong>no claim of a
			profitable edge</strong>. Its value is that it can prove the truth about a strategy — including
			the truth that a strategy has none — with machinery most systems never apply to themselves.
		</p>
	</Card>

	<Card eyebrow="Provably true" title="Engineering & representation">
		<div class="tiles">
			{#each proven as p (p.label)}
				<StatTile label={p.label} value={p.value} sub={p.sub} tone="accent" />
			{/each}
		</div>
	</Card>

	<Card eyebrow="The headline finding" title="Survivorship bias manufactured the entire apparent edge">
		{#snippet action()}
			<Badge variant="warn" dot>NO EDGE DEMONSTRATED</Badge>
		{/snippet}
		<p class="lede">
			The same cross-sectional strategy, measured four ways over an identical out-of-sample window
			(2023–2026). Once the companies that were removed, acquired or went bankrupt are included —
			and traded only while they were real index members — the apparent edge disappears.
		</p>
		<div class="table-wrap">
			<table>
				<thead>
					<tr><th>Evaluation</th><th class="num">Sharpe (OOS)</th><th>Read</th></tr>
				</thead>
				<tbody>
					{#each evaluations as e (e.name)}
						<tr>
							<td><span class="ename">{e.name}</span><span class="edetail">{e.detail}</span></td>
							<td class="num mono" class:down={e.tone === 'down'} class:up={e.tone === 'up'}>{e.sharpe}</td>
							<td class="note">{e.note}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="foot-note">
			Rigorous technical and fundamental signals on the survivorship-free S&P 500 did not, over this
			window, beat a simple buy-and-hold. That is consistent with efficient markets — and it is the
			honest result. The negative finding <em>is</em> the achievement: almost no one proves their own
			backtest is a mirage.
		</p>
	</Card>

	<Card eyebrow="How every claim is tested" title="Methodology">
		<ul class="method">
			{#each methodology as [name, desc] (name)}
				<li><span class="mname">{name}</span><span class="mdesc">{desc}</span></li>
			{/each}
		</ul>
	</Card>

	<Card eyebrow="The bar for real capital" title="Unchanged and absolute">
		<p class="lede">
			A strategy reaches live capital only after it clears Levels 1–6 <strong>survivorship-free</strong>,
			then survives <strong>Level 7</strong> (3–6 months paper trading), with the risk firewall retaining
			final authority and a human sign-off. Nothing here is close to that bar — and the platform says so,
			plainly, which is the point.
		</p>
	</Card>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}
	.lede {
		margin: 0;
		color: var(--text-muted);
		line-height: 1.6;
		font-size: 13.5px;
		max-width: 78ch;
	}
	.tiles {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 12px;
	}
	.table-wrap {
		overflow-x: auto;
		margin-top: 14px;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
		min-width: 480px;
	}
	th {
		text-align: left;
		font-size: 11px;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-faint);
		padding: 8px 12px;
		border-bottom: 1px solid var(--border);
	}
	th.num,
	td.num {
		text-align: right;
	}
	td {
		padding: 11px 12px;
		border-bottom: 1px solid var(--border);
		color: var(--text-muted);
		vertical-align: top;
	}
	.ename {
		display: block;
		color: var(--text);
		font-weight: 600;
	}
	.edetail {
		display: block;
		font-size: 11.5px;
		color: var(--text-faint);
		margin-top: 2px;
	}
	td.num {
		font-weight: 700;
		font-size: 14px;
	}
	td.down {
		color: var(--short, #ff5f73);
	}
	td.up {
		color: var(--long, #2fe08a);
	}
	.note {
		font-size: 12px;
		color: var(--text-dim);
	}
	.foot-note {
		margin: 16px 0 0;
		font-size: 12.5px;
		line-height: 1.6;
		color: var(--text-dim);
		max-width: 82ch;
	}
	.method {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.method li {
		display: grid;
		grid-template-columns: 200px 1fr;
		gap: 14px;
		align-items: baseline;
	}
	.mname {
		color: var(--accent);
		font-weight: 600;
		font-size: 13px;
	}
	.mdesc {
		color: var(--text-muted);
		font-size: 13px;
		line-height: 1.5;
	}
	@media (max-width: 640px) {
		.method li {
			grid-template-columns: 1fr;
			gap: 2px;
		}
	}
</style>
