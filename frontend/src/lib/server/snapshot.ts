/**
 * Builds the full dashboard snapshot in one place so every page load and the
 * polling API share identical logic. SERVER ONLY.
 */

import type { DashboardSnapshot } from '$lib/types';
import { runPipeline } from '$lib/server/aurora';
import { getMode, getUniverse } from '$lib/server/config';
import { fetchQuotes, hasApiKey, type FetchLike } from '$lib/server/fmp';

export async function buildSnapshot(fetchFn: FetchLike): Promise<DashboardSnapshot> {
	const universe = getUniverse();
	const mode = getMode();

	const { quotes, source } = await fetchQuotes(universe, fetchFn);
	return runPipeline(quotes, { mode, hasApiKey: hasApiKey(), dataSource: source });
}
