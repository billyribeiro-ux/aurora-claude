/**
 * AURORA-SWING instrument universe.
 *
 * Mirrors the "Additional context" universe from the deployment protocol:
 * market ETFs, macro instruments and sector ETFs, plus a tradable large-cap
 * equity set the signal engine acts on. `base` prices seed the synthetic
 * fallback used when no FMP key is configured.
 */

export type UniverseGroup = 'market' | 'macro' | 'sector' | 'equity';

export interface InstrumentMeta {
	name: string;
	base: number;
	group: UniverseGroup;
}

export const UNIVERSE_META: Record<string, InstrumentMeta> = {
	// Market
	SPY: { name: 'S&P 500 ETF', base: 592, group: 'market' },
	QQQ: { name: 'Nasdaq 100 ETF', base: 522, group: 'market' },
	IWM: { name: 'Russell 2000 ETF', base: 228, group: 'market' },

	// Macro
	'^VIX': { name: 'CBOE Volatility Index', base: 15.5, group: 'macro' },
	'^TNX': { name: '10Y Treasury Yield', base: 4.28, group: 'macro' },
	UUP: { name: 'US Dollar Index ETF', base: 29.4, group: 'macro' },
	GLD: { name: 'Gold Trust', base: 246, group: 'macro' },
	USO: { name: 'US Oil Fund', base: 78, group: 'macro' },

	// Sectors
	XLK: { name: 'Technology', base: 238, group: 'sector' },
	XLF: { name: 'Financials', base: 50, group: 'sector' },
	XLV: { name: 'Health Care', base: 146, group: 'sector' },
	XLE: { name: 'Energy', base: 92, group: 'sector' },
	XLI: { name: 'Industrials', base: 142, group: 'sector' },
	XLY: { name: 'Consumer Discretionary', base: 218, group: 'sector' },
	XLP: { name: 'Consumer Staples', base: 82, group: 'sector' },

	// Tradable equities
	NVDA: { name: 'NVIDIA Corp', base: 138, group: 'equity' },
	AAPL: { name: 'Apple Inc', base: 232, group: 'equity' },
	MSFT: { name: 'Microsoft Corp', base: 452, group: 'equity' },
	AMD: { name: 'Advanced Micro Devices', base: 168, group: 'equity' },
	GOOGL: { name: 'Alphabet Inc', base: 178, group: 'equity' },
	AMZN: { name: 'Amazon.com Inc', base: 212, group: 'equity' },
	META: { name: 'Meta Platforms', base: 612, group: 'equity' },
	TSLA: { name: 'Tesla Inc', base: 342, group: 'equity' },
	AVGO: { name: 'Broadcom Inc', base: 224, group: 'equity' },
	SMCI: { name: 'Super Micro Computer', base: 42, group: 'equity' }
};

export const BENCHMARKS = ['SPY', 'QQQ', 'IWM'] as const;
export const MACRO = ['^VIX', '^TNX', 'UUP', 'GLD', 'USO'] as const;
export const SECTORS = ['XLK', 'XLF', 'XLV', 'XLE', 'XLI', 'XLY', 'XLP'] as const;
export const TRADABLE = [
	'NVDA',
	'AAPL',
	'MSFT',
	'AMD',
	'GOOGL',
	'AMZN',
	'META',
	'TSLA',
	'AVGO',
	'SMCI'
] as const;

/** Full universe the console tracks by default. */
export const DEFAULT_UNIVERSE: string[] = [
	...BENCHMARKS,
	...MACRO,
	...SECTORS,
	...TRADABLE
];

export function symbolsFromEnv(raw: string | undefined): string[] {
	if (!raw) return DEFAULT_UNIVERSE;
	const parsed = raw
		.split(',')
		.map((s) => s.trim().toUpperCase())
		.filter(Boolean);
	return parsed.length > 0 ? parsed : DEFAULT_UNIVERSE;
}

export function groupOf(symbol: string): UniverseGroup {
	return UNIVERSE_META[symbol]?.group ?? 'equity';
}

export function nameOf(symbol: string): string {
	return UNIVERSE_META[symbol]?.name ?? symbol;
}
