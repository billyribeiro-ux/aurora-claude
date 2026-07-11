/**
 * Financial Modeling Prep (FMP) data client — SERVER ONLY.
 *
 * Lives under `$lib/server` so SvelteKit guarantees it can never be bundled
 * into client code. The API key is read at runtime from `$env/dynamic/private`
 * (i.e. `process.env.FMP_API_KEY` under adapter-node), so the user can supply it
 * after deployment without a rebuild.
 *
 * When no key is present the client returns clearly-labelled SYNTHETIC data so
 * the console stays fully functional for review. Real data flows in the moment
 * `FMP_API_KEY` is set.
 */

import { env } from '$env/dynamic/private';
import type { Candle, DataSource, Quote } from '$lib/types';
import { UNIVERSE_META } from '$lib/universe';

// FMP "stable" API (the legacy /api/v3 endpoints are retired for post-2025 keys).
const BASE = 'https://financialmodelingprep.com/stable';

export type FetchLike = typeof fetch;

export function hasApiKey(): boolean {
	return Boolean(env.FMP_API_KEY && env.FMP_API_KEY.trim().length > 0);
}

/** Shape of a single FMP `/quote` record (only the fields we consume). */
interface FmpQuote {
	symbol: string;
	name?: string;
	price?: number;
	change?: number;
	changePercentage?: number;
	dayLow?: number;
	dayHigh?: number;
	yearHigh?: number;
	yearLow?: number;
	open?: number;
	previousClose?: number;
	volume?: number;
	avgVolume?: number;
	marketCap?: number | null;
	priceAvg50?: number;
	priceAvg200?: number;
	timestamp?: number;
}

/** One row of the stable /historical-price-eod/full response (newest first). */
interface FmpHistoricalBar {
	date: string;
	open: number;
	high: number;
	low: number;
	close: number;
	volume: number;
}

function num(value: number | undefined | null, fallback = 0): number {
	return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

/**
 * Deterministic pseudo-random in [0,1) seeded by a string. Used only for the
 * synthetic fallback so the demo is stable across reloads (no Math.random).
 */
function seeded(seed: string): () => number {
	let h = 2166136261;
	for (let i = 0; i < seed.length; i++) {
		h ^= seed.charCodeAt(i);
		h = Math.imul(h, 16777619);
	}
	return () => {
		h += 0x6d2b79f5;
		let t = h;
		t = Math.imul(t ^ (t >>> 15), t | 1);
		t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

/** Build a short synthetic sparkline anchored on a base price. */
function synthSpark(symbol: string, base: number, drift: number, points = 30): number[] {
	const rnd = seeded(symbol + ':spark');
	const out: number[] = [];
	let p = base * (1 - drift * 0.6);
	const step = (base * drift) / points;
	for (let i = 0; i < points; i++) {
		p += step + (rnd() - 0.5) * base * 0.006;
		out.push(Number(p.toFixed(2)));
	}
	out[out.length - 1] = base;
	return out;
}

function syntheticQuote(symbol: string): Quote {
	const meta = UNIVERSE_META[symbol] ?? { name: symbol, base: 100 };
	const rnd = seeded(symbol + ':quote');
	const base = meta.base;
	const changePercent = Number(((rnd() - 0.45) * 3.4).toFixed(2));
	const price = Number((base * (1 + changePercent / 100)).toFixed(2));
	const change = Number((price - base).toFixed(2));
	const dayRange = base * (0.008 + rnd() * 0.02);
	return {
		symbol,
		name: meta.name,
		price,
		change,
		changePercent,
		dayLow: Number((price - dayRange * rnd()).toFixed(2)),
		dayHigh: Number((price + dayRange * rnd()).toFixed(2)),
		yearLow: Number((base * (0.62 + rnd() * 0.15)).toFixed(2)),
		yearHigh: Number((base * (1.15 + rnd() * 0.25)).toFixed(2)),
		open: Number((base * (1 + (rnd() - 0.5) * 0.01)).toFixed(2)),
		previousClose: base,
		volume: Math.round(2_000_000 + rnd() * 40_000_000),
		avgVolume: Math.round(5_000_000 + rnd() * 30_000_000),
		marketCap: Math.round(base * 1e9 * (1 + rnd() * 40)),
		spark: synthSpark(symbol, price, changePercent / 100),
		timestamp: 0
	};
}

function toQuote(q: FmpQuote): Quote {
	const price = num(q.price, num(q.previousClose));
	const changePercent = num(q.changePercentage);
	return {
		symbol: q.symbol,
		name: q.name ?? UNIVERSE_META[q.symbol]?.name ?? q.symbol,
		price,
		change: num(q.change),
		changePercent,
		dayLow: num(q.dayLow, price),
		dayHigh: num(q.dayHigh, price),
		yearLow: num(q.yearLow, price),
		yearHigh: num(q.yearHigh, price),
		open: num(q.open, price),
		previousClose: num(q.previousClose, price),
		volume: num(q.volume),
		avgVolume: num(q.avgVolume),
		marketCap: q.marketCap ?? null,
		spark: synthSpark(q.symbol, price, changePercent / 100),
		timestamp: num(q.timestamp)
	};
}

export interface QuoteResult {
	quotes: Quote[];
	/** What actually produced the data — 'FMP' only if the live fetch succeeded. */
	source: DataSource;
}

/** Fetch batched quotes for `symbols`. Falls back to synthetic data on error. */
export async function fetchQuotes(symbols: string[], fetchFn: FetchLike): Promise<QuoteResult> {
	if (symbols.length === 0) return { quotes: [], source: hasApiKey() ? 'FMP' : 'SYNTHETIC' };

	if (!hasApiKey()) {
		return { quotes: symbols.map(syntheticQuote), source: 'SYNTHETIC' };
	}

	try {
		const symbolParam = symbols.map(encodeURIComponent).join(',');
		const url = `${BASE}/batch-quote?symbols=${symbolParam}&apikey=${env.FMP_API_KEY}`;
		const res = await fetchFn(url);
		if (!res.ok) throw new Error(`FMP quote HTTP ${res.status}`);
		const data = (await res.json()) as FmpQuote[];
		if (!Array.isArray(data) || data.length === 0) throw new Error('FMP quote empty');

		const bySymbol = new Map(data.map((q) => [q.symbol, toQuote(q)]));
		// Preserve requested order; synthesize any the provider omitted.
		return { quotes: symbols.map((s) => bySymbol.get(s) ?? syntheticQuote(s)), source: 'FMP' };
	} catch (err) {
		console.warn('[fmp] quote fetch failed, using synthetic data:', (err as Error).message);
		return { quotes: symbols.map(syntheticQuote), source: 'SYNTHETIC' };
	}
}

function syntheticCandles(symbol: string, days: number): Candle[] {
	const meta = UNIVERSE_META[symbol] ?? { name: symbol, base: 100 };
	const rnd = seeded(symbol + ':candles');
	const out: Candle[] = [];
	let close = meta.base * (0.82 + rnd() * 0.1);
	const now = Date.now(); // anchor synthetic history to "today"
	const drift = (meta.base - close) / days;
	for (let i = days - 1; i >= 0; i--) {
		const open = close;
		const move = drift + (rnd() - 0.48) * meta.base * 0.018;
		close = Math.max(1, open + move);
		const high = Math.max(open, close) * (1 + rnd() * 0.01);
		const low = Math.min(open, close) * (1 - rnd() * 0.01);
		const date = new Date(now - i * 86_400_000).toISOString().slice(0, 10);
		out.push({
			date,
			open: Number(open.toFixed(2)),
			high: Number(high.toFixed(2)),
			low: Number(low.toFixed(2)),
			close: Number(close.toFixed(2)),
			volume: Math.round(3_000_000 + rnd() * 25_000_000)
		});
	}
	// Anchor the last close to the synthetic quote so the chart and the
	// watchlist agree in demo mode (real data is naturally consistent).
	const tail = out[out.length - 1];
	if (tail) {
		const target = syntheticQuote(symbol).price;
		tail.close = target;
		tail.high = Number(Math.max(tail.high, target).toFixed(2));
		tail.low = Number(Math.min(tail.low, target).toFixed(2));
	}
	return out;
}

/** Fetch daily candles (oldest → newest). Falls back to synthetic on error. */
export async function fetchHistorical(
	symbol: string,
	fetchFn: FetchLike,
	days = 120
): Promise<Candle[]> {
	if (!hasApiKey()) {
		return syntheticCandles(symbol, days);
	}

	try {
		// Bound the payload to roughly `days` trading rows via a `from` date
		// (1.6× calendar days covers weekends/holidays).
		const from = new Date(Date.now() - Math.ceil(days * 1.6) * 86_400_000)
			.toISOString()
			.slice(0, 10);
		const url = `${BASE}/historical-price-eod/full?symbol=${encodeURIComponent(symbol)}&from=${from}&apikey=${env.FMP_API_KEY}`;
		const res = await fetchFn(url);
		if (!res.ok) throw new Error(`FMP historical HTTP ${res.status}`);
		const data = (await res.json()) as FmpHistoricalBar[];
		const rows = Array.isArray(data) ? data : [];
		if (rows.length === 0) throw new Error('FMP historical empty');

		// Stable API returns newest → oldest; take the most recent `days` and
		// reverse for chronological order.
		return rows
			.slice(0, days)
			.reverse()
			.map((r) => ({
				date: r.date,
				open: num(r.open),
				high: num(r.high),
				low: num(r.low),
				close: num(r.close),
				volume: num(r.volume)
			}));
	} catch (err) {
		console.warn('[fmp] historical fetch failed, using synthetic data:', (err as Error).message);
		return syntheticCandles(symbol, days);
	}
}
