<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title?: string;
		eyebrow?: string;
		tight?: boolean;
		children: Snippet;
		action?: Snippet;
	}

	let { title, eyebrow, tight = false, children, action }: Props = $props();
</script>

<section class="card">
	{#if title || eyebrow || action}
		<header class="card-head">
			<div class="titles">
				{#if eyebrow}<span class="eyebrow">{eyebrow}</span>{/if}
				{#if title}<h3>{title}</h3>{/if}
			</div>
			{#if action}<div class="action">{@render action()}</div>{/if}
		</header>
	{/if}
	<div class="card-body" class:tight>
		{@render children()}
	</div>
</section>

<style>
	.card {
		display: flex;
		flex-direction: column;
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 40%), var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-sm);
		overflow: hidden;
	}
	.card-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
		padding: 16px 18px 0;
	}
	.titles {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	h3 {
		font-size: 14px;
		font-weight: 600;
		color: var(--text);
	}
	.action {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-shrink: 0;
	}
	.card-body {
		padding: 16px 18px 18px;
	}
	.card-body.tight {
		padding: 0;
	}
</style>
