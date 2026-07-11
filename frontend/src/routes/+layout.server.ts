import type { LayoutServerLoad } from './$types';
import type { DataSource } from '$lib/types';
import { getMode } from '$lib/server/config';
import { hasApiKey } from '$lib/server/fmp';

/** Lightweight shell config (no market fetch) shared by every page. */
export const load: LayoutServerLoad = () => {
	const keyed = hasApiKey();
	const dataSource: DataSource = keyed ? 'FMP' : 'SYNTHETIC';
	return {
		mode: getMode(),
		hasApiKey: keyed,
		dataSource
	};
};
