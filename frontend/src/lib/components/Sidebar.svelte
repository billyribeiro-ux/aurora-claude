<script lang="ts">
	import { page } from '$app/state';

	interface NavItem {
		href: string;
		label: string;
		icon: string;
	}

	const items: NavItem[] = [
		{ href: '/', label: 'Command', icon: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z' },
		{ href: '/signals', label: 'Signals', icon: 'M3 12h4l3 8 4-16 3 8h4' },
		{ href: '/markets', label: 'Markets', icon: 'M3 3v18h18M7 14l4-4 3 3 5-6' },
		{ href: '/backtest', label: 'Backtest', icon: 'M9 14 4 9l5-5M4 9h11a5 5 0 0 1 0 10h-3' },
		{ href: '/monitoring', label: 'Monitor', icon: 'M3 12h4l2-5 4 12 2-7h6' },
		{ href: '/architecture', label: 'Arch', icon: 'M12 2 2 7l10 5 10-5zM2 12l10 5 10-5M2 17l10 5 10-5' },
		{
			href: '/protocol',
			label: 'Protocol',
			icon: 'M5 4a2 2 0 0 1 2-2h12v18H7a2 2 0 0 0-2 2zM19 2v18'
		}
	];

	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}
</script>

<aside class="sidebar">
	<a class="brand" href="/">
		<span class="mark" aria-hidden="true">
			<svg viewBox="0 0 24 24" width="22" height="22">
				<path d="M3 18c3-9 6-9 9 0s6 9 9 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
			</svg>
		</span>
		<span class="wordmark">AURORA</span>
	</a>

	<nav>
		{#each items as item (item.href)}
			<a href={item.href} class="item" class:active={isActive(item.href)} aria-current={isActive(item.href) ? 'page' : undefined}>
				<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
					<path d={item.icon} fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
				</svg>
				<span class="label">{item.label}</span>
			</a>
		{/each}
	</nav>

	<div class="foot">
		<span class="ver mono">SWING · v0.1</span>
	</div>
</aside>

<style>
	.sidebar {
		display: flex;
		flex-direction: column;
		width: 92px;
		flex-shrink: 0;
		background: color-mix(in srgb, var(--surface) 82%, black);
		border-right: 1px solid var(--border);
		padding: 18px 0;
		position: sticky;
		top: 0;
		height: 100vh;
	}
	.brand {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		padding: 0 8px 20px;
		color: var(--accent);
	}
	.mark {
		display: grid;
		place-items: center;
		width: 40px;
		height: 40px;
		border-radius: 12px;
		background: var(--accent-soft);
		border: 1px solid var(--accent-line);
	}
	.wordmark {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.16em;
		color: var(--text);
	}
	nav {
		display: flex;
		flex-direction: column;
		gap: 4px;
		padding: 8px;
		flex: 1;
	}
	.item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 5px;
		padding: 11px 4px;
		border-radius: var(--radius);
		color: var(--text-dim);
		transition: all 0.15s ease;
	}
	.item:hover {
		color: var(--text);
		background: var(--surface-2);
	}
	.item.active {
		color: var(--accent);
		background: var(--accent-soft);
	}
	.label {
		font-size: 10.5px;
		font-weight: 600;
		letter-spacing: 0.02em;
	}
	.foot {
		display: flex;
		justify-content: center;
		padding-top: 8px;
	}
	.ver {
		font-size: 9px;
		color: var(--text-faint);
		letter-spacing: 0.08em;
	}
	@media (max-width: 720px) {
		.sidebar {
			flex-direction: row;
			width: 100%;
			height: auto;
			padding: 8px;
			align-items: center;
			overflow-x: auto;
		}
		.brand {
			flex-direction: row;
			padding: 0 12px 0 6px;
		}
		nav {
			flex-direction: row;
			padding: 0;
		}
		.item {
			flex-direction: row;
			padding: 8px 12px;
		}
		.foot {
			display: none;
		}
	}
</style>
