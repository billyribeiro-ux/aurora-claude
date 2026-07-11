import type { PageServerLoad } from './$types';
import { buildSnapshot } from '$lib/server/snapshot';
import { fetchHistorical } from '$lib/server/fmp';
import { nameOf } from '$lib/universe';

export const load: PageServerLoad = async ({ fetch }) => {
	const snapshot = await buildSnapshot(fetch);
	const initialSymbol = 'SPY';
	const initialCandles = await fetchHistorical(initialSymbol, fetch, 120);
	return {
		snapshot,
		initialSymbol,
		initialName: nameOf(initialSymbol),
		initialCandles,
		pageTitle: 'Markets',
		pageSubtitle: 'Live universe · price action & context'
	};
};
