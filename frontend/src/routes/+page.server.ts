import type { PageServerLoad } from './$types';
import { buildSnapshot } from '$lib/server/snapshot';

export const load: PageServerLoad = async ({ fetch }) => {
	const snapshot = await buildSnapshot(fetch);
	return {
		snapshot,
		pageTitle: 'Command Center',
		pageSubtitle: 'Autonomous decision pipeline · live overview'
	};
};
