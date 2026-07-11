<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import Badge from '$lib/components/Badge.svelte';

	const phases = [
		{ n: 0, title: 'Data Acquisition', body: '10+ years of daily / 4H / 1H OHLCV. Start with the S&P 500, expand to the Russell 3000. Add market (SPY, QQQ, IWM), macro (VIX, TNX, DXY, gold, oil) and sector ETF context.' },
		{ n: 1, title: 'Foundation Model', body: 'Self-supervised pretraining — masked modelling + contrastive learning + future-latent prediction. ~2–8 weeks of GPU time. Output: a market-understanding model.' },
		{ n: 2, title: 'World Model', body: 'Learn "what happens next" — map past market states to future latent states. Must beat a random forecast, a momentum baseline and buy-and-hold.' },
		{ n: 3, title: 'RL Training', body: 'Millions of simulated episodes in the historical market simulator. The agent learns when to enter, when to stay out, how to size and when to exit.' },
		{ n: 4, title: 'Walk-Forward Certification', body: '5+ years of unseen data spanning every regime — bull (2017/2020/2023), bear (2018/2022) and crisis (2020 COVID, 2022 inflation).' },
		{ n: 5, title: 'Paper Trading', body: '3–6 months, no exceptions. Monitor live slippage, execution assumptions, signal quality and confidence calibration before any capital.' }
	];

	const validation = [
		{ level: 1, title: 'Data Integrity', body: 'No future leakage. Timestamps ordered, features from past data only, corporate actions and survivorship handled.' },
		{ level: 2, title: 'Model Validation', body: 'Representation quality — mask reconstruction, latent stability (similar setups cluster) and future-latent MSE.' },
		{ level: 3, title: 'Strategy Validation', body: 'Beat buy-and-hold, momentum, an MA system and a random agent. Report CAGR, Sharpe, Sortino, Calmar, profit factor and expectancy.' },
		{ level: 4, title: 'Regime-Specific', body: 'Performance broken down by bull, bear, high-volatility and sideways environments — weakness cannot hide in an aggregate.' },
		{ level: 5, title: 'Monte Carlo Stress', body: '10,000 trade-order shuffles, 2×–10× slippage, ±5% overnight gaps and 5–20% missing data.' },
		{ level: 6, title: 'Statistical Significance', body: 'Bootstrap 95% confidence intervals on returns and a low probability of backtest overfitting (PBO).' },
		{ level: 7, title: 'Live Deployment Criteria', body: 'Paper-trading passed, risk limits verified, uncertainty acceptable, regime detection stable, emergency shutdown tested.' }
	];

	const targets = [
		{ tier: 'Conservative', cagr: '10–20%', dd: '< 15%', sharpe: '1.0–1.5', variant: 'info' as const },
		{ tier: 'Strong', cagr: '20–35%', dd: '10–20%', sharpe: '1.5–2.0', variant: 'ok' as const },
		{ tier: 'Exceptional', cagr: '35%+', dd: 'controlled', sharpe: '2.0+', variant: 'accent' as const }
	];

	const limits = [
		{ title: 'Alpha decay', body: 'Once a pattern is known, capital flows exploit it and the edge fades.' },
		{ title: 'Data quality', body: 'Bad prices, missing data and survivorship bias create false intelligence.' },
		{ title: 'Overfitting', body: 'A powerful model can memorise history. Walk-forward, regularization and a simplicity preference are the defence.' },
		{ title: 'Execution reality', body: 'Spreads, liquidity, partial fills and gaps can turn a 20% backtest into 12–15% live.' },
		{ title: 'Black swans', body: 'No model predicts the never-before-seen. The risk engine exists precisely because prediction is impossible.' }
	];

	const checklist = [
		'Walk forward passed',
		'Monte Carlo passed',
		'No leakage',
		'Risk limits verified',
		'Paper trading passed',
		'Model uncertainty acceptable',
		'Regime detection stable',
		'Execution tested',
		'Emergency shutdown tested'
	];
</script>

<div class="page">
	<Card eyebrow="Positioning" title="What this system actually is">
		<p class="lede">
			AURORA-SWING is not a prediction machine. It is an adaptive, probabilistic decision system that
			identifies favourable risk/reward opportunities while continuously adapting to changing market
			environments. Its strongest advantage is not calling price direction — it is avoiding poor
			environments, sizing intelligently, recognising regime change and controlling downside.
		</p>
	</Card>

	<section class="block">
		<h2 class="section-title">Training Sequence</h2>
		<div class="phase-grid">
			{#each phases as p (p.n)}
				<div class="phase">
					<div class="phase-head">
						<span class="phase-n mono">PHASE {p.n}</span>
						<h3>{p.title}</h3>
					</div>
					<p>{p.body}</p>
				</div>
			{/each}
		</div>
	</section>

	<section class="block">
		<h2 class="section-title">Validation Framework</h2>
		<div class="levels">
			{#each validation as v (v.level)}
				<div class="level">
					<span class="level-n mono">L{v.level}</span>
					<div class="level-body">
						<h3>{v.title}</h3>
						<p>{v.body}</p>
					</div>
				</div>
			{/each}
		</div>
	</section>

	<section class="block">
		<h2 class="section-title">Realistic Performance Targets</h2>
		<div class="targets">
			{#each targets as t (t.tier)}
				<div class="target">
					<Badge variant={t.variant}>{t.tier}</Badge>
					<dl>
						<div><dt>CAGR</dt><dd class="mono">{t.cagr}</dd></div>
						<div><dt>Max Drawdown</dt><dd class="mono">{t.dd}</dd></div>
						<div><dt>Sharpe</dt><dd class="mono">{t.sharpe}</dd></div>
					</dl>
				</div>
			{/each}
		</div>
		<p class="caveat">
			No responsible researcher promises guaranteed returns, 90% win rates or unlimited scalability —
			those claims usually indicate overfitting. Achieving the above consistently is extremely
			difficult.
		</p>
	</section>

	<div class="two">
		<Card eyebrow="Honest Assessment" title="What will limit performance">
			<ul class="limits">
				{#each limits as l (l.title)}
					<li>
						<span class="l-title">{l.title}</span>
						<span class="l-body">{l.body}</span>
					</li>
				{/each}
			</ul>
		</Card>

		<Card eyebrow="Go / No-Go" title="Production Approval Checklist">
			<ul class="check">
				{#each checklist as item (item)}
					<li><span class="box" aria-hidden="true">☐</span>{item}</li>
				{/each}
			</ul>
			<p class="foot-note">The system cannot deploy because "the backtest looked good".</p>
		</Card>
	</div>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 24px;
	}
	.lede {
		margin: 0;
		color: var(--text-muted);
		line-height: 1.7;
		font-size: 14px;
		max-width: 90ch;
	}
	.block {
		display: flex;
		flex-direction: column;
		gap: 14px;
	}
	.section-title {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--text-dim);
	}
	.phase-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 14px;
	}
	.phase {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 16px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		border-top: 2px solid var(--accent-line);
	}
	.phase-head h3 {
		font-size: 15px;
		margin-top: 2px;
	}
	.phase-n {
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.12em;
		color: var(--accent);
	}
	.phase p {
		margin: 0;
		font-size: 13px;
		line-height: 1.6;
		color: var(--text-muted);
	}
	.levels {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.level {
		display: flex;
		gap: 16px;
		padding: 14px 16px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}
	.level-n {
		font-size: 14px;
		font-weight: 700;
		color: var(--accent);
		flex-shrink: 0;
		width: 32px;
	}
	.level-body h3 {
		font-size: 14px;
	}
	.level-body p {
		margin: 4px 0 0;
		font-size: 13px;
		line-height: 1.6;
		color: var(--text-muted);
	}
	.targets {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 14px;
	}
	.target {
		display: flex;
		flex-direction: column;
		gap: 12px;
		padding: 18px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}
	.target dl {
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.target dl > div {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		border-bottom: 1px solid var(--border);
		padding-bottom: 6px;
	}
	.target dt {
		font-size: 12px;
		color: var(--text-dim);
	}
	.target dd {
		margin: 0;
		font-weight: 600;
		font-size: 14px;
	}
	.caveat {
		margin: 0;
		font-size: 13px;
		line-height: 1.6;
		color: var(--text-dim);
		max-width: 90ch;
	}
	.two {
		display: grid;
		grid-template-columns: 1.3fr 1fr;
		gap: 20px;
		align-items: start;
	}
	.limits {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 14px;
	}
	.limits li {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.l-title {
		font-weight: 600;
		font-size: 13.5px;
	}
	.l-body {
		font-size: 13px;
		color: var(--text-muted);
		line-height: 1.5;
	}
	.check {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.check li {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 13px;
		color: var(--text-muted);
	}
	.box {
		color: var(--accent);
		font-size: 15px;
	}
	.foot-note {
		margin: 16px 0 0;
		padding-top: 14px;
		border-top: 1px solid var(--border);
		font-size: 12.5px;
		font-style: italic;
		color: var(--text-dim);
	}
	@media (max-width: 900px) {
		.two {
			grid-template-columns: 1fr;
		}
	}
</style>
