<script lang="ts">
	interface Props {
		hasApiKey: boolean;
	}

	let { hasApiKey }: Props = $props();

	let dismissed = $state(false);
</script>

{#if !hasApiKey && !dismissed}
	<div class="banner" role="status">
		<span class="icon" aria-hidden="true">◆</span>
		<p>
			Running in <strong>synthetic data mode</strong>. Add your Financial Modeling Prep key —
			<code>FMP_API_KEY</code> in <code>.env</code> — to stream live market data. The key stays
			server-side and is never sent to the browser.
		</p>
		<button type="button" onclick={() => (dismissed = true)} aria-label="Dismiss">✕</button>
	</div>
{/if}

<style>
	.banner {
		display: flex;
		align-items: center;
		gap: 12px;
		margin: 0 28px;
		margin-top: 20px;
		padding: 10px 14px;
		background: var(--warn-soft);
		border: 1px solid rgba(255, 176, 32, 0.3);
		border-radius: var(--radius);
		font-size: 13px;
		color: var(--text-muted);
	}
	.icon {
		color: var(--warn);
	}
	p {
		margin: 0;
		flex: 1;
		line-height: 1.5;
	}
	strong {
		color: var(--text);
	}
	code {
		font-family: var(--font-mono);
		font-size: 12px;
		background: var(--surface-3);
		padding: 1px 5px;
		border-radius: 4px;
		color: var(--accent);
	}
	button {
		background: transparent;
		border: none;
		color: var(--text-dim);
		font-size: 14px;
		padding: 4px 6px;
		border-radius: 4px;
	}
	button:hover {
		color: var(--text);
		background: var(--surface-3);
	}
	@media (max-width: 720px) {
		.banner {
			margin: 16px;
		}
	}
</style>
