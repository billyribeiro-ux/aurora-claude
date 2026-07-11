import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { buildSnapshot } from '$lib/server/snapshot';

/**
 * Live dashboard snapshot for client-side polling. The FMP key never leaves the
 * server; the browser only ever sees the computed, key-free JSON payload.
 */
export const GET: RequestHandler = async ({ fetch, setHeaders }) => {
	const snapshot = await buildSnapshot(fetch);
	setHeaders({ 'cache-control': 'no-store' });
	return json(snapshot);
};
