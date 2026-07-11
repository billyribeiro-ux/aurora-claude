import { error, json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { runBacktest } from '$lib/server/backtest';

const MAX_SPAN_DAYS = 730; // 2-year cap to bound compute / payload
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Replay the decision engine over [from, to] and return the signals it would
 * have produced with simulated outcomes. The FMP key stays server-side.
 */
export const GET: RequestHandler = async ({ url, fetch, setHeaders }) => {
	const from = (url.searchParams.get('from') ?? '').trim();
	const to = (url.searchParams.get('to') ?? '').trim();
	const symbol = (url.searchParams.get('symbol') ?? '').toUpperCase().trim() || null;

	if (!DATE_RE.test(from) || !DATE_RE.test(to)) {
		error(400, 'from and to must be YYYY-MM-DD dates');
	}
	if (from >= to) {
		error(400, 'from must be before to');
	}
	const span = (Date.parse(to) - Date.parse(from)) / 86_400_000;
	if (span > MAX_SPAN_DAYS) {
		error(400, `date range too large (max ${MAX_SPAN_DAYS} days ≈ 2 years)`);
	}

	const result = await runBacktest({ from, to, symbol }, fetch);
	setHeaders({ 'cache-control': 'no-store' });
	return json(result);
};
