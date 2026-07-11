<script lang="ts">
	import '../app.css';
	import type { Snippet } from 'svelte';
	import { page } from '$app/state';
	import type { LayoutServerData } from './$types';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import TopBar from '$lib/components/TopBar.svelte';
	import DataModeBanner from '$lib/components/DataModeBanner.svelte';

	interface Props {
		data: LayoutServerData;
		children: Snippet;
	}

	let { data, children }: Props = $props();

	const title = $derived(page.data.pageTitle ?? 'Command Center');
	const subtitle = $derived(page.data.pageSubtitle);
	// Prefer the source the page actually fetched; fall back to configured state.
	const dataSource = $derived(page.data.snapshot?.status.dataSource ?? data.dataSource);
</script>

<div class="shell">
	<Sidebar />
	<div class="main">
		<TopBar mode={data.mode} {dataSource} {title} {subtitle} />
		<DataModeBanner hasApiKey={data.hasApiKey} />
		<main class="content">
			{@render children()}
		</main>
	</div>
</div>

<style>
	.shell {
		display: flex;
		min-height: 100vh;
	}
	.main {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
	}
	.content {
		padding: 24px 28px 48px;
		max-width: var(--maxw);
		width: 100%;
	}
	@media (max-width: 720px) {
		.shell {
			flex-direction: column;
		}
		.content {
			padding: 16px;
		}
	}
</style>
