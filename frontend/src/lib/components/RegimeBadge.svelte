<script lang="ts">
	import Badge from './Badge.svelte';
	import type { RegimeName } from '$lib/types';
	import { regimeLabel } from '$lib/format';

	interface Props {
		regime: RegimeName;
		pulse?: boolean;
	}

	let { regime, pulse = false }: Props = $props();

	type Variant = 'long' | 'short' | 'critical' | 'warn' | 'neutral' | 'info';

	const variant: Variant = $derived.by(() => {
		switch (regime) {
			case 'BULL_TREND':
				return 'long';
			case 'BEAR_TREND':
				return 'short';
			case 'CRISIS':
				return 'critical';
			case 'HIGH_VOLATILITY':
				return 'warn';
			case 'RECOVERY':
				return 'info';
			default:
				return 'neutral';
		}
	});
</script>

<Badge {variant} dot {pulse}>{regimeLabel(regime)}</Badge>
