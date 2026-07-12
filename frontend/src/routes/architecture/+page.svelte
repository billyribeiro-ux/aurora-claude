<script lang="ts">
	import Card from '$lib/components/Card.svelte';
	import Badge from '$lib/components/Badge.svelte';
	import Disclosure from '$lib/components/Disclosure.svelte';

	const flow = [
		{ tag: 'Perceive', label: 'Foundation Encoder', desc: 'Hierarchical transformer → latent state z(t)' },
		{ tag: 'Simulate', label: 'World Model', desc: 'z(t+1…t+20), scenarios + uncertainty' },
		{ tag: 'Classify', label: 'Regime Engine', desc: 'HMM + latent clustering + neural head' },
		{ tag: 'Decide', label: 'RL Policy', desc: 'PPO + SAC → entry, size, stops, exits' },
		{ tag: 'Constrain', label: 'Risk Firewall', desc: 'Independent override authority' },
		{ tag: 'Execute', label: 'Execution', desc: 'Paper → Live' },
		{ tag: 'Learn', label: 'Continual Loop', desc: 'Replay + error analysis → selective updates' }
	];

	const marketState = [
		{ k: 'Trend', v: '+0.82', bar: 0.91, tone: 'up' },
		{ k: 'Momentum', v: '+0.61', bar: 0.8, tone: 'up' },
		{ k: 'Volatility', v: 'Increasing', bar: 0.7, tone: 'warn' },
		{ k: 'Breadth', v: 'Weakening', bar: 0.4, tone: 'down' },
		{ k: 'Liquidity', v: 'Normal', bar: 0.55, tone: 'flat' },
		{ k: 'Inst. Flow', v: 'Accumulating', bar: 0.78, tone: 'up' }
	];
	const regimeProbs = [
		{ k: 'Bull Trend', v: 72 },
		{ k: 'Distribution', v: 18 },
		{ k: 'Reversal', v: 10 }
	];

	const scenarios = [
		{ name: 'Continuation', prob: 48, ret: '+4.2%', tone: 'up' },
		{ name: 'Pullback', prob: 37, ret: '−2.1%', tone: 'down' },
		{ name: 'Volatility Event', prob: 15, ret: '−5.8%', tone: 'down' }
	];

	const regimes = [
		{
			name: 'Momentum',
			char: 'Trending sectors · expanding breadth · low correlation',
			behavior: 'Hold winners longer · wider stops · larger sizing'
		},
		{
			name: 'Mean Reversion',
			char: 'Range-bound · failed breakouts · oscillation',
			behavior: 'Smaller positions · faster exits · tight targets'
		},
		{
			name: 'Crisis',
			char: 'VIX spike · correlation explosion · gap risk',
			behavior: 'Reduce exposure · raise cash · disable entries'
		}
	];

	const actionGroups = [
		{ label: 'Entry', items: ['Long', 'Short'] },
		{ label: 'Size', items: ['0%', '10%', '25%', '50%', '75%', '100%'] },
		{ label: 'Stop', items: ['1 ATR', '1.5', '2', '3'] },
		{ label: 'Target', items: ['1R', '2R', '3R', 'Dyn'] },
		{ label: 'Trail', items: ['None', 'ATR', 'Structural'] },
		{ label: 'Exit', items: ['Hold', 'Reduce', 'Close'] }
	];

	const selfEval = [
		'Was my decision correct?',
		'Was my reasoning correct?',
		'Did the regime change?',
		'Did my model misunderstand something?',
		'Did risk management save me?'
	];

	const specs = [
		{ title: 'Foundation Encoder', rows: [['Local', '6L · 256d · 8h · 1024 FFN'], ['Global', '8L · 512d · 16h · 2048 FFN'], ['Loss', '0.4 mask · 0.3 contrastive · 0.3 predictive'], ['Optim', 'AdamW · 3e-4 · bf16']] },
		{ title: 'World Model', rows: [['Dynamics', '12L · 512d · 16h · ctx 128'], ['Outputs', 'ẑ(t+k) · reward · uncertainty σ'], ['Loss', 'L_z + 0.5·L_r + 0.2·L_u']] },
		{ title: 'RL Policy', rows: [['Algorithm', 'PPO + SAC hybrid'], ['Params', 'clip 0.2 · γ 0.995 · λ 0.95'], ['Reward', 'R = P − D − G − T − E']] },
		{ title: 'Regime Ensemble', rows: [['HMM', '40%'], ['Latent clustering', '40%'], ['Neural head', '20%']] },
		{ title: 'Risk Firewall', rows: [['Portfolio heat', '5%'], ['Single position', '2%'], ['Sector', '20%'], ['Correlation', '> 0.85 → trim'], ['Vol target', '15% annualized']] }
	];

	const safety = [
		'exceed portfolio risk limits',
		'trade during unknown model states',
		'bypass risk controls',
		'train on future information',
		'use future labels',
		'optimise only historical returns'
	];

	const naive = ['Price', 'Technical Indicators', 'Neural Network', 'Buy / Sell'];
	const aurora = [
		'Market Data',
		'Representation Learning',
		'Market Understanding',
		'Scenario Simulation',
		'Regime Awareness',
		'Risk-Constrained Decision',
		'Continuous Learning'
	];
</script>

<div class="page">
	<Disclosure kind="design" />

	<Card eyebrow="AURORA-SWING" title="Autonomous market intelligence, not price prediction">
		<p class="lede">
			A self-learning platform for <strong>3–20 day</strong> swing horizons. It does not attempt
			deterministic price prediction — it learns market-state representations, regimes, future
			probability distributions and risk-adjusted decisions. The core principle:
			<em>representation before prediction</em>, and <em>risk has final authority</em>.
		</p>
	</Card>

	<section class="block">
		<h2 class="section-title">System Flow</h2>
		<div class="flow">
			{#each flow as stage, i (stage.tag)}
				<div class="stage">
					<span class="tag">{stage.tag}</span>
					<span class="label">{stage.label}</span>
					<span class="desc">{stage.desc}</span>
				</div>
				{#if i < flow.length - 1}<span class="arrow" aria-hidden="true">→</span>{/if}
			{/each}
		</div>
	</section>

	<section class="block">
		<h2 class="section-title">The Five Intelligence Layers</h2>
		<div class="layers">
			<!-- Layer 1 -->
			<Card>
				<div class="layer-head"><span class="ln mono">01</span><div><h3>Market Perception</h3><span class="tagline">Equivalent to human vision</span></div></div>
				<p class="ltext">The model does not see "price went up." It reads a market-state vector.</p>
				<div class="statevec">
					{#each marketState as s (s.k)}
						<div class="sv-row">
							<span class="sv-k">{s.k}</span>
							<span class="sv-track"><span class="sv-fill {s.tone}" style:width="{s.bar * 100}%"></span></span>
							<span class="sv-v mono {s.tone}">{s.v}</span>
						</div>
					{/each}
				</div>
				<div class="probs">
					{#each regimeProbs as p (p.k)}
						<div class="prob"><span class="mono">{p.v}%</span><span>{p.k}</span></div>
					{/each}
				</div>
			</Card>

			<!-- Layer 2 -->
			<Card>
				<div class="layer-head"><span class="ln mono">02</span><div><h3>Market World Model</h3><span class="tagline">The most important component</span></div></div>
				<p class="ltext">Instead of "will tomorrow go up?", it asks "what are the possible futures?"</p>
				<div class="scenarios">
					{#each scenarios as sc (sc.name)}
						<div class="sc">
							<div class="sc-top"><span class="sc-name">{sc.name}</span><span class="sc-ret mono {sc.tone}">{sc.ret}</span></div>
							<div class="sc-track"><span class="sc-fill {sc.tone}" style:width="{sc.prob}%"></span></div>
							<span class="sc-prob mono">p = {sc.prob}%</span>
						</div>
					{/each}
				</div>
			</Card>

			<!-- Layer 3 -->
			<Card>
				<div class="layer-head"><span class="ln mono">03</span><div><h3>Regime Intelligence</h3><span class="tagline">"What game are we playing?"</span></div></div>
				<div class="regimes">
					{#each regimes as r (r.name)}
						<div class="regime">
							<span class="r-name">{r.name}</span>
							<span class="r-char">{r.char}</span>
							<span class="r-beh">{r.behavior}</span>
						</div>
					{/each}
				</div>
			</Card>

			<!-- Layer 4 -->
			<Card>
				<div class="layer-head"><span class="ln mono">04</span><div><h3>RL Decision System</h3><span class="tagline">Maximise risk-adjusted growth</span></div></div>
				<p class="ltext">The agent does not predict price — it chooses actions.</p>
				<div class="actions">
					{#each actionGroups as g (g.label)}
						<div class="ag">
							<span class="ag-label">{g.label}</span>
							<div class="chips">
								{#each g.items as it (it)}<span class="chip mono">{it}</span>{/each}
							</div>
						</div>
					{/each}
				</div>
			</Card>

			<!-- Layer 5 -->
			<Card>
				<div class="layer-head"><span class="ln mono">05</span><div><h3>Autonomous Improvement</h3><span class="tagline">Selective, never blind</span></div></div>
				<p class="ltext">After every trade the system interrogates itself, then updates selectively.</p>
				<ul class="eval">
					{#each selfEval as q (q)}<li>{q}</li>{/each}
				</ul>
				<p class="warn-note">It does <strong>not</strong> retrain every night — that is how models destroy themselves.</p>
			</Card>
		</div>
	</section>

	<section class="block">
		<h2 class="section-title">Technical Specifications</h2>
		<div class="specs">
			{#each specs as s (s.title)}
				<div class="spec">
					<h4>{s.title}</h4>
					<dl>
						{#each s.rows as row, i (i)}
							<div><dt>{row[0]}</dt><dd class="mono">{row[1]}</dd></div>
						{/each}
					</dl>
				</div>
			{/each}
		</div>
	</section>

	<div class="two">
		<Card eyebrow="Non-negotiable" title="Safety Rules">
			<p class="ltext">The system must <strong>never</strong>:</p>
			<ul class="safety">
				{#each safety as rule (rule)}<li><span class="x" aria-hidden="true">✕</span>{rule}</li>{/each}
			</ul>
		</Card>

		<Card eyebrow="Why it's different" title="Retail AI vs AURORA-SWING">
			<div class="compare">
				<div class="col naive">
					<Badge variant="short">Most retail AI</Badge>
					<div class="chain">
						{#each naive as n, i (n)}
							<span class="node">{n}</span>{#if i < naive.length - 1}<span class="down">↓</span>{/if}
						{/each}
					</div>
					<span class="fail">markets change · features decay · overfits · no risk intelligence</span>
				</div>
				<div class="col aurora">
					<Badge variant="ok">AURORA-SWING</Badge>
					<div class="chain">
						{#each aurora as a, i (a)}
							<span class="node hot">{a}</span>{#if i < aurora.length - 1}<span class="down">↓</span>{/if}
						{/each}
					</div>
				</div>
			</div>
		</Card>
	</div>
</div>

<style>
	.page { display: flex; flex-direction: column; gap: 24px; }
	.lede { margin: 0; color: var(--text-muted); line-height: 1.7; font-size: 14px; max-width: 92ch; }
	.lede strong { color: var(--text); }
	.lede em { color: var(--accent); font-style: normal; }
	.block { display: flex; flex-direction: column; gap: 14px; }
	.section-title { font-size: 13px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); }

	.flow { display: flex; align-items: stretch; gap: 4px; overflow-x: auto; padding-bottom: 4px; }
	.stage { display: flex; flex-direction: column; gap: 4px; flex: 1 1 0; min-width: 150px; padding: 12px 14px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); border-top: 2px solid var(--accent-line); }
	.tag { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
	.stage .label { font-size: 13px; font-weight: 600; }
	.stage .desc { font-size: 11px; color: var(--text-dim); line-height: 1.4; }
	.arrow { align-self: center; color: var(--text-faint); flex-shrink: 0; }

	.layers { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
	.layer-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
	.ln { font-size: 20px; font-weight: 700; color: var(--accent); }
	.layer-head h3 { font-size: 16px; }
	.tagline { font-size: 11px; color: var(--text-dim); }
	.ltext { margin: 0 0 12px; font-size: 12.5px; color: var(--text-muted); line-height: 1.5; }

	.statevec { display: flex; flex-direction: column; gap: 7px; }
	.sv-row { display: grid; grid-template-columns: 78px 1fr auto; align-items: center; gap: 10px; font-size: 12px; }
	.sv-k { color: var(--text-dim); }
	.sv-track { height: 5px; background: var(--surface-3); border-radius: 999px; overflow: hidden; }
	.sv-fill { display: block; height: 100%; border-radius: 999px; }
	.sv-fill.up { background: var(--up); }
	.sv-fill.down { background: var(--down); }
	.sv-fill.warn { background: var(--warn); }
	.sv-fill.flat { background: var(--flat); }
	.sv-v { font-weight: 600; }
	.sv-v.up { color: var(--up); }
	.sv-v.down { color: var(--down); }
	.sv-v.warn { color: var(--warn); }
	.probs { display: flex; gap: 8px; margin-top: 14px; }
	.prob { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 8px; background: var(--surface-2); border-radius: var(--radius-sm); font-size: 11px; color: var(--text-dim); }
	.prob .mono { font-size: 15px; font-weight: 700; color: var(--text); }

	.scenarios { display: flex; flex-direction: column; gap: 12px; }
	.sc-top { display: flex; justify-content: space-between; font-size: 13px; }
	.sc-name { font-weight: 600; }
	.sc-ret.up { color: var(--up); }
	.sc-ret.down { color: var(--down); }
	.sc-track { height: 6px; background: var(--surface-3); border-radius: 999px; overflow: hidden; margin: 5px 0 3px; }
	.sc-fill { display: block; height: 100%; }
	.sc-fill.up { background: var(--up); }
	.sc-fill.down { background: var(--down); }
	.sc-prob { font-size: 11px; color: var(--text-dim); }

	.regimes { display: flex; flex-direction: column; gap: 10px; }
	.regime { display: flex; flex-direction: column; gap: 3px; padding: 10px 12px; background: var(--surface-2); border-radius: var(--radius-sm); border-left: 2px solid var(--accent-line); }
	.r-name { font-weight: 600; font-size: 13px; }
	.r-char, .r-beh { font-size: 11.5px; color: var(--text-dim); line-height: 1.4; }
	.r-beh { color: var(--text-muted); }

	.actions { display: flex; flex-direction: column; gap: 10px; }
	.ag { display: grid; grid-template-columns: 60px 1fr; align-items: center; gap: 10px; }
	.ag-label { font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.06em; }
	.chips { display: flex; flex-wrap: wrap; gap: 5px; }
	.chip { font-size: 11px; padding: 3px 8px; background: var(--surface-3); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text-muted); }

	.eval { list-style: none; margin: 0 0 12px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
	.eval li { font-size: 12.5px; color: var(--text-muted); padding-left: 16px; position: relative; }
	.eval li::before { content: '›'; position: absolute; left: 0; color: var(--accent); }
	.warn-note { margin: 0; font-size: 12px; color: var(--text-dim); }
	.warn-note strong { color: var(--warn); }

	.specs { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
	.spec { padding: 16px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
	.spec h4 { font-size: 13px; margin-bottom: 10px; color: var(--accent); }
	.spec dl { margin: 0; display: flex; flex-direction: column; gap: 7px; }
	.spec dl > div { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
	.spec dt { font-size: 11.5px; color: var(--text-dim); flex-shrink: 0; }
	.spec dd { margin: 0; font-size: 11.5px; text-align: right; color: var(--text-muted); }

	.two { display: grid; grid-template-columns: 1fr 1.1fr; gap: 20px; align-items: start; }
	.safety { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
	.safety li { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--text-muted); }
	.x { color: var(--critical); font-weight: 700; }

	.compare { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
	.col { display: flex; flex-direction: column; gap: 10px; align-items: flex-start; }
	.chain { display: flex; flex-direction: column; gap: 4px; width: 100%; }
	.node { font-size: 12px; padding: 6px 10px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text-muted); text-align: center; }
	.node.hot { border-color: var(--accent-line); color: var(--text); }
	.down { text-align: center; color: var(--text-faint); font-size: 11px; }
	.fail { font-size: 11px; color: var(--down); line-height: 1.4; }

	@media (max-width: 900px) {
		.two, .compare { grid-template-columns: 1fr; }
	}
</style>
