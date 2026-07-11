import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { fetchHistorical } from '$lib/server/fmp';
import { UNIVERSE_META } from '$lib/universe';

/** Daily OHLCV history for one instrument (chronological). */
export const GET: RequestHandler = async ({ url, fetch, setHeaders }) => {
	const symbol = (url.searchParams.get('symbol') ?? '').toUpperCase().trim();
	if (!symbol) error(400, 'symbol query parameter is required');

	const days = Math.min(Math.max(Number(url.searchParams.get('days') ?? '120') || 120, 20), 400);

	const candles = await fetchHistorical(symbol, fetch, days);
	setHeaders({ 'cache-control': 'no-store' });
	return json({ symbol, name: UNIVERSE_META[symbol]?.name ?? symbol, candles });
};
