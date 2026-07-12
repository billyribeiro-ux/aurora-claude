<script lang="ts">
	/**
	 * Honest disclosure about what is actually producing the numbers on screen.
	 * `kind="signals"` for pages that show live engine output; `kind="design"`
	 * for pages that describe the target (not-yet-built) architecture.
	 */
	interface Props {
		kind?: 'signals' | 'design';
	}

	let { kind = 'signals' }: Props = $props();
</script>

<aside class="disclosure" role="note">
	<span class="icon" aria-hidden="true">ⓘ</span>
	{#if kind === 'signals'}
		<p>
			These signals come from a <strong>transparent, rule-based heuristic engine</strong> — not a
			trained model. “Confidence” is a heuristic score, <strong>not a calibrated probability</strong>.
			Out-of-sample evaluation found <strong>no statistically significant edge</strong> yet
			(module&nbsp;12). Portfolio figures are simulated. For research and education only —
			<strong>not financial advice</strong>.
		</p>
	{:else}
		<p>
			This describes AURORA’s <strong>target architecture</strong>. The live console currently runs a
			transparent heuristic baseline; the trained stack (foundation model, world model, RL policy) is
			<strong>not yet built or validated</strong> — no statistically significant edge has been
			demonstrated. Descriptions below are the design, not a running trained model.
		</p>
	{/if}
</aside>

<style>
	.disclosure {
		display: flex;
		align-items: flex-start;
		gap: 10px;
		padding: 11px 14px;
		background: var(--surface-2);
		border: 1px solid var(--border);
		border-left: 3px solid var(--accent);
		border-radius: var(--radius);
		font-size: 12.5px;
		color: var(--text-muted);
	}
	.icon {
		color: var(--accent);
		font-size: 14px;
		line-height: 1.5;
		flex-shrink: 0;
	}
	p {
		margin: 0;
		line-height: 1.55;
		max-width: 88ch;
	}
	strong {
		color: var(--text);
		font-weight: 600;
	}
</style>
