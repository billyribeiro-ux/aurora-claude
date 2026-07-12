import { test, expect, type APIRequestContext } from '@playwright/test';

/**
 * Data-integrity, reproducibility and no-look-ahead-leakage guarantees for the
 * decision engine — the properties that make the backtest trustworthy.
 *
 * These need live FMP data. To stay CI-robust under provider rate limits they
 * retry until live data is available (server-side caching makes repeats free),
 * and SKIP (rather than flake) if the provider is hard-limited during a run.
 */

const DECISION_FIELDS = [
	'symbol',
	'date',
	'direction',
	'score',
	'confidence',
	'positionSize',
	'stopDistance',
	'targetDistance',
	'approved',
	'price'
] as const;

type Sig = Record<string, unknown>;
const keyOf = (s: Sig): string => DECISION_FIELDS.map((k) => s[k]).join('|');
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function getBacktest(request: APIRequestContext, url: string): Promise<any> {
	const res = await request.get(url);
	return res.ok() ? await res.json() : null;
}

/** Retry until the backtest is served from live FMP data (or give up). */
async function getLiveBacktest(request: APIRequestContext, url: string, tries = 15): Promise<any> {
	for (let i = 0; i < tries; i++) {
		const j = await getBacktest(request, url);
		if (j && j.dataSource === 'FMP') return j;
		await sleep(1200);
	}
	return null;
}

test('backtest is reproducible (deterministic for identical inputs)', async ({ request }) => {
	const url = '/api/backtest?from=2026-01-05&to=2026-04-01';
	const a = await getLiveBacktest(request, url);
	test.skip(!a, 'FMP live data unavailable (rate-limited) during this run');
	const b = await getBacktest(request, url); // server-cached → same live data
	expect(a.signals.length).toBeGreaterThan(0);
	expect(b.signals.map(keyOf).sort()).toEqual(a.signals.map(keyOf).sort());
});

test('no look-ahead leakage: adding future data does not change past decisions', async ({
	request
}) => {
	const short = await getLiveBacktest(request, '/api/backtest?from=2026-01-05&to=2026-04-01');
	const long = await getLiveBacktest(request, '/api/backtest?from=2026-01-05&to=2026-07-01');
	test.skip(!short || !long, 'FMP live data unavailable (rate-limited) during this run');

	const longByKey = new Map<string, Sig>(long.signals.map((s: Sig) => [`${s.date}|${s.symbol}`, s]));
	let overlap = 0;
	for (const s of short.signals as Sig[]) {
		const l = longByKey.get(`${s.date}|${s.symbol}`);
		if (!l) continue;
		overlap++;
		for (const f of DECISION_FIELDS) {
			expect(l[f], `${f} @ ${s.date} ${s.symbol} must be unchanged by future data`).toEqual(s[f]);
		}
	}
	expect(overlap, 'the two windows should share early-period decisions').toBeGreaterThan(0);
});

const FMP_KEY: string =
	typeof process !== 'undefined' && process.env.FMP_API_KEY ? process.env.FMP_API_KEY : '';

test('console EOD data matches the raw FMP source exactly', async ({ request }) => {
	test.skip(!FMP_KEY, 'requires FMP_API_KEY (live-data integrity check)');
	const symbols = ['SPY', 'NVDA', 'AAPL'];

	let verified = false;
	let sawBug = false;
	for (let attempt = 0; attempt < 15 && !verified && !sawBug; attempt++) {
		let allMatch = true;
		for (const sym of symbols) {
			const rawRes = await request.get(
				`https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=${sym}&from=2026-01-01&to=2026-07-10&apikey=${FMP_KEY}`
			);
			const raw = rawRes.ok() ? ((await rawRes.json()) as Array<Record<string, number | string>>) : null;
			if (!Array.isArray(raw) || raw.length === 0) {
				allMatch = false; // raw side rate-limited — retry
				break;
			}
			const rawByDate = new Map(raw.map((b) => [b.date as string, b]));

			const con = await (await request.get(`/api/history?symbol=${sym}&days=200`)).json();
			if (con.source && con.source !== 'FMP') {
				allMatch = false; // console served synthetic (rate-limited) — retry
				break;
			}
			const shared = (con.candles as Array<Record<string, number | string>>).filter((c) =>
				rawByDate.has(c.date as string)
			);
			if (shared.length < 20) {
				allMatch = false;
				break;
			}
			for (const c of shared) {
				const r = rawByDate.get(c.date as string)!;
				if (c.close !== r.close || c.open !== r.open || c.high !== r.high || c.low !== r.low) {
					// Console reported FMP data that disagrees with the source → real defect.
					sawBug = true;
					expect(c.close, `${sym} ${c.date} close (console vs raw FMP)`).toBe(r.close);
				}
			}
		}
		if (allMatch) verified = true;
		else if (!sawBug) await sleep(1500);
	}
	test.skip(!verified && !sawBug, 'FMP live data unavailable (rate-limited) during this run');
	expect(verified).toBe(true);
});
