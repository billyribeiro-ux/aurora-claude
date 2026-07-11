import type { PageServerLoad } from './$types';
import { buildSnapshot } from '$lib/server/snapshot';

export const load: PageServerLoad = async ({ fetch }) => {
	const snapshot = await buildSnapshot(fetch);
	return {
		snapshot,
		pageTitle: 'Signals',
		pageSubtitle: 'RL policy proposals filtered by the risk firewall'
	};
};
