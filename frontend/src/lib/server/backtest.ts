/**
 * AURORA-SWING backtest engine — SERVER ONLY, fully additive.
 *
 * Replays the **existing** live decision engine (`detectRegime` +
 * `generateSignals`, imported read-only) over a historical [from, to] window and
 * reports the signals it would have produced, plus a simulated outcome for each
 * approved trade.
 *
 * Leakage safety:
 *   - Every point-in-time ("as-of") quote is built from bars with index <= D,
 *     so the decision on day D never sees the future.
 *   - Trade outcomes are simulated from bars AFTER the entry — used only to
 *     score what happened, never fed back into signal generation.
 *
 * The live engine (`aurora.ts`) and live pages are untouched by this module.
 */

import type {
	BacktestOutcome,
	BacktestResult,
	BacktestSignal,
	BacktestSummary,
	Candle,
	Direction,
	EquityPoint,
	Quote,
	RegimePoint
} from '$lib/types';
import { detectRegime, generateSignals } from '$lib/server/aurora';
import { fetchHistoricalRange, hasApiKey, type FetchLike } from '$lib/server/fmp';
import { BENCHMARKS, SECTORS, TRADABLE, nameOf } from '$lib/universe';

const LOOKBACK_DAYS = 260; // trading-day lookback for 52w range / avg volume
const HOLD_DAYS = 20; // max holding window for outcome simulation
const SIGNAL_CAP = 750; // max signals returned to the client

// Universe needed to reproduce the live decision: benchmarks + VIX (regime) +
// sectors (breadth) + tradable equities (signals). Pure-macro names are omitted.
const BACKTEST_UNIVERSE: string[] = [...BENCHMARKS, '^VIX', ...SECTORS, ...TRADABLE];

const mean = (xs: number[]): number => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);

function addDays(iso: string, n: number): string {
	return new Date(Date.parse(iso) + n * 86_400_000).toISOString().slice(0, 10);
}

function todayISO(): string {
	return new Date().toISOString().slice(0, 10);
}

/** Largest index with candles[i].date <= date (candles ascending by date). */
function lastIndexOnOrBefore(candles: Candle[], date: string): number {
	let lo = 0;
	let hi = candles.length - 1;
	let ans = -1;
	while (lo <= hi) {
		const mid = (lo + hi) >> 1;
		if (candles[mid].date <= date) {
			ans = mid;
			lo = mid + 1;
		} else {
			hi = mid - 1;
		}
	}
	return ans;
}

/** Build a point-in-time Quote from bars up to and including `idx`. */
function buildAsOfQuote(symbol: string, candles: Candle[], idx: number): Quote {
	const bar = candles[idx];
	const prev = idx > 0 ? candles[idx - 1] : bar;
	const change = bar.close - prev.close;
	const changePercent = prev.close ? (change / prev.close) * 100 : 0;

	const window = candles.slice(Math.max(0, idx - 251), idx + 1);
	const yearHigh = Math.max(...window.map((c) => c.high));
	const yearLow = Math.min(...window.map((c) => c.low));

	const volWindow = candles.slice(Math.max(0, idx - 49), idx + 1);
	const avgVolume = mean(volWindow.map((c) => c.volume));

	const spark = candles.slice(Math.max(0, idx - 29), idx + 1).map((c) => c.close);

	return {
		symbol,
		name: nameOf(symbol),
		price: bar.close,
		change,
		changePercent,
		dayLow: bar.low,
		dayHigh: bar.high,
		yearLow,
		yearHigh,
		open: bar.open,
		previousClose: prev.close,
		volume: bar.volume,
		avgVolume,
		marketCap: null,
		spark,
		timestamp: Date.parse(bar.date)
	};
}

interface Sim {
	outcome: BacktestOutcome;
	realizedReturn: number;
	exitDate: string | null;
	holdDays: number;
}

/** Simulate an approved trade forward from `entryIdx` (outcome measurement only). */
function simulateOutcome(
	direction: Direction,
	entry: number,
	stopDistance: number,
	targetDistance: number,
	candles: Candle[],
	entryIdx: number
): Sim {
	const long = direction > 0;
	const target = long ? entry * (1 + targetDistance) : entry * (1 - targetDistance);
	const stop = long ? entry * (1 - stopDistance) : entry * (1 + stopDistance);
	const lastIdx = Math.min(entryIdx + HOLD_DAYS, candles.length - 1);

	if (lastIdx <= entryIdx) {
		return { outcome: 'open', realizedReturn: 0, exitDate: null, holdDays: 0 };
	}

	for (let j = entryIdx + 1; j <= lastIdx; j++) {
		const bar = candles[j];
		// Conservative: if a bar touches both, assume the stop filled first.
		if (long) {
			if (bar.low <= stop) return { outcome: 'stop', realizedReturn: -stopDistance, exitDate: bar.date, holdDays: j - entryIdx };
			if (bar.high >= target) return { outcome: 'target', realizedReturn: targetDistance, exitDate: bar.date, holdDays: j - entryIdx };
		} else {
			if (bar.high >= stop) return { outcome: 'stop', realizedReturn: -stopDistance, exitDate: bar.date, holdDays: j - entryIdx };
			if (bar.low <= target) return { outcome: 'target', realizedReturn: targetDistance, exitDate: bar.date, holdDays: j - entryIdx };
		}
	}

	const exitBar = candles[lastIdx];
	const raw = (exitBar.close - entry) / entry;
	return {
		outcome: 'timeout',
		realizedReturn: long ? raw : -raw,
		exitDate: exitBar.date,
		holdDays: lastIdx - entryIdx
	};
}

export async function runBacktest(
	opts: { from: string; to: string; symbol?: string | null },
	fetchFn: FetchLike
): Promise<BacktestResult> {
	const from = opts.from;
	const to = opts.to;
	const symbolFilter =
		opts.symbol && (TRADABLE as readonly string[]).includes(opts.symbol) ? opts.symbol : null;

	// Fetch a lookback before `from` (indicators) and a buffer after `to` so
	// late signals can still resolve — capped at today.
	const fetchFrom = addDays(from, -Math.ceil(LOOKBACK_DAYS * 1.6));
	const bufferedTo = addDays(to, Math.ceil(HOLD_DAYS * 1.6));
	const today = todayISO();
	const fetchTo = bufferedTo < today ? bufferedTo : today;

	const series = new Map<string, Candle[]>();
	const byDate = new Map<string, Map<string, number>>();
	await Promise.all(
		BACKTEST_UNIVERSE.map(async (s) => {
			const candles = await fetchHistoricalRange(s, fetchFn, fetchFrom, fetchTo);
			series.set(s, candles);
			byDate.set(s, new Map(candles.map((c, i) => [c.date, i])));
		})
	);

	// Backtest trading days = SPY's dates inside [from, to].
	const spy = series.get('SPY') ?? [];
	const dates = spy.filter((c) => c.date >= from && c.date <= to).map((c) => c.date);

	const signals: BacktestSignal[] = [];
	const regimeTimeline: RegimePoint[] = [];
	// Per-symbol "in a position until this exit date" — prevents re-entering a
	// name every day it keeps signalling, so trades don't overlap.
	const busyUntil = new Map<string, string>();
	let proposals = 0;
	let approvedCount = 0;

	for (const date of dates) {
		const quotes: Quote[] = [];
		for (const s of BACKTEST_UNIVERSE) {
			const candles = series.get(s);
			const idxMap = byDate.get(s);
			if (!candles || !idxMap) continue;
			const idx = idxMap.get(date) ?? lastIndexOnOrBefore(candles, date);
			if (idx < 0) continue;
			quotes.push(buildAsOfQuote(s, candles, idx));
		}
		if (quotes.length === 0) continue;

		const regime = detectRegime(quotes);
		regimeTimeline.push({ date, regime: regime.regime, confidence: regime.confidence });

		for (const sig of generateSignals(quotes, regime)) {
			if (sig.direction === 0) continue;
			if (symbolFilter && sig.symbol !== symbolFilter) continue;
			proposals++;
			if (!sig.approved) continue;
			approvedCount++;

			// Skip if we're already holding this symbol (no overlapping entries).
			const busy = busyUntil.get(sig.symbol);
			if (busy && date <= busy) continue;

			const candles = series.get(sig.symbol);
			const idxMap = byDate.get(sig.symbol);
			if (!candles || !idxMap) continue;
			const entryIdx = idxMap.get(date) ?? lastIndexOnOrBefore(candles, date);
			if (entryIdx < 0) continue;

			const entry = candles[entryIdx].close;
			const sim = simulateOutcome(
				sig.direction,
				entry,
				sig.stopDistance,
				sig.targetDistance,
				candles,
				entryIdx
			);

			// Block re-entry into this symbol until the trade exits (or window end).
			busyUntil.set(sig.symbol, sim.exitDate ?? to);

			signals.push({
				date,
				symbol: sig.symbol,
				direction: sig.direction,
				score: sig.score,
				confidence: sig.confidence,
				positionSize: sig.positionSize,
				stopDistance: sig.stopDistance,
				targetDistance: sig.targetDistance,
				regime: sig.regime,
				approved: true,
				price: entry,
				outcome: sim.outcome,
				realizedReturn: Number(sim.realizedReturn.toFixed(4)),
				exitDate: sim.exitDate,
				holdDays: sim.holdDays
			});
		}
	}

	// Equity curve from closed trades, ordered by exit date (compounded, size-weighted).
	const closed = signals
		.filter((s) => s.outcome !== 'open' && s.exitDate)
		.slice()
		.sort((a, b) => (a.exitDate! < b.exitDate! ? -1 : a.exitDate! > b.exitDate! ? 1 : 0));

	let equity = 1;
	let peak = 1;
	let maxDrawdown = 0;
	const equityCurve: EquityPoint[] = [{ date: from, equity: 1 }];
	for (const t of closed) {
		equity *= 1 + t.positionSize * t.realizedReturn;
		peak = Math.max(peak, equity);
		maxDrawdown = Math.min(maxDrawdown, equity / peak - 1);
		equityCurve.push({ date: t.exitDate as string, equity: Number(equity.toFixed(4)) });
	}

	const returns = closed.map((t) => t.realizedReturn);
	const wins = returns.filter((r) => r > 0).length;
	const summary: BacktestSummary = {
		from,
		to,
		tradingDays: dates.length,
		proposals,
		approved: approvedCount,
		entered: signals.length,
		closed: closed.length,
		wins,
		losses: closed.length - wins,
		winRate: closed.length ? wins / closed.length : 0,
		avgReturn: Number(mean(returns).toFixed(4)),
		expectancy: Number(mean(closed.map((t) => t.positionSize * t.realizedReturn)).toFixed(4)),
		totalReturn: Number((equity - 1).toFixed(4)),
		maxDrawdown: Number(maxDrawdown.toFixed(4)),
		bestTrade: returns.length ? Math.max(...returns) : 0,
		worstTrade: returns.length ? Math.min(...returns) : 0,
		avgHoldDays: Number(mean(closed.map((t) => t.holdDays)).toFixed(1))
	};

	// Most recent signals first; cap the payload.
	signals.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));

	return {
		summary,
		signals: signals.slice(0, SIGNAL_CAP),
		equityCurve,
		regimeTimeline,
		dataSource: hasApiKey() ? 'FMP' : 'SYNTHETIC',
		symbolFilter,
		truncated: signals.length > SIGNAL_CAP
	};
}
