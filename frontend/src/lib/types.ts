/**
 * AURORA-SWING — shared type contract.
 *
 * These types mirror the Python deployment layer (Module 10) so the console can
 * be pointed at the real inference service without changing the UI:
 *
 *   - `TradingSignal`  ↔  10_deployment/signal_service.py::TradingSignal
 *   - `RegimeState`    ↔  03_regime_engine output
 *   - `HealthReport`   ↔  10_deployment/monitoring.py::ModelMonitor
 *
 * The decision flow is always: encode → forecast → regime → RL → risk firewall.
 */

export type Direction = -1 | 0 | 1;

export type RegimeName =
	| 'BULL_TREND'
	| 'BEAR_TREND'
	| 'HIGH_VOLATILITY'
	| 'SIDEWAYS'
	| 'CRISIS'
	| 'RECOVERY';

export type SystemMode = 'LIVE' | 'PAPER' | 'DEMO';
export type DataSource = 'FMP' | 'SYNTHETIC';

/** A single price/quote snapshot for one instrument. */
export interface Quote {
	symbol: string;
	name: string;
	price: number;
	change: number;
	changePercent: number;
	dayLow: number;
	dayHigh: number;
	yearLow: number;
	yearHigh: number;
	open: number;
	previousClose: number;
	volume: number;
	avgVolume: number;
	marketCap: number | null;
	/** Recent closes (oldest → newest) for sparklines. */
	spark: number[];
	timestamp: number;
}

/** One OHLCV bar. */
export interface Candle {
	date: string;
	open: number;
	high: number;
	low: number;
	close: number;
	volume: number;
}

/**
 * A structured trading decision. Field-for-field compatible with the Python
 * `TradingSignal.to_dict()` payload (camelCased for the TS side).
 */
export interface TradingSignal {
	symbol: string;
	timestamp: string; // ISO-8601
	direction: Direction; // +1 long, -1 short, 0 flat
	confidence: number; // [0,1] = 1 - world-model uncertainty
	positionSize: number; // fraction of risk budget
	stopDistance: number; // fraction of price
	targetDistance: number; // fraction of price
	regime: RegimeName;
	approved: boolean; // final risk-firewall decision
	/** Human-readable reasons — the explainability trail behind the decision. */
	rationale: string[];
	/** Raw conviction score in [-1, 1] before risk sizing. */
	score: number;
	/** Latest price the signal was computed against. */
	price: number;
	expectedReward: number; // target/stop reward:risk ratio
}

export interface RegimeState {
	regime: RegimeName;
	confidence: number; // [0,1]
	since: string; // ISO-8601
	volatility: number; // annualized, e.g. 0.18 = 18%
	trendStrength: number; // [-1, 1]
	breadth: number; // [0, 1] fraction of universe advancing
	description: string;
	/** Recommended maximum gross exposure for this regime, [0,1]. */
	exposureCap: number;
}

export interface HealthMetrics {
	drawdown: number; // [0,1]
	uncertainty: number; // [0,1] world-model uncertainty
	rewardDecay: number; // [0,1]
	drift: number; // [0,1]
	portfolioHeat: number; // [0,1] sum of open risk
	sharpe: number;
}

export type AlertCode =
	| 'MAX_DRAWDOWN_WARNING'
	| 'MODEL_UNCERTAINTY_HIGH'
	| 'PERFORMANCE_DEGRADATION'
	| 'MODEL_DRIFT_DETECTED';

export type HealthStatus = 'HEALTHY' | 'WATCH' | 'DEGRADED' | 'HALT';

export interface HealthReport {
	status: HealthStatus;
	metrics: HealthMetrics;
	alerts: AlertCode[];
}

/** One node in the inference pipeline status strip. */
export interface PipelineStage {
	key: string;
	label: string;
	status: 'ok' | 'active' | 'warn' | 'idle';
	detail: string;
	latencyMs: number;
}

export interface PortfolioSnapshot {
	equity: number;
	cash: number;
	grossExposure: number; // fraction
	netExposure: number; // fraction
	openPositions: number;
	dayPnl: number;
	dayPnlPct: number;
	totalReturnPct: number;
	maxDrawdownPct: number;
	sharpe: number;
	sortino: number;
	winRate: number; // [0,1]
}

export type EventLevel = 'info' | 'success' | 'warn' | 'critical';

export interface EventEntry {
	time: string; // ISO-8601
	level: EventLevel;
	message: string;
}

/** Everything the dashboard needs in one server round-trip. */
export interface DashboardSnapshot {
	status: SystemStatus;
	signals: TradingSignal[];
	quotes: Quote[];
}

/** The full snapshot rendered by the console. */
export interface SystemStatus {
	mode: SystemMode;
	dataSource: DataSource;
	asOf: string; // ISO-8601
	hasApiKey: boolean;
	regime: RegimeState;
	health: HealthReport;
	portfolio: PortfolioSnapshot;
	pipeline: PipelineStage[];
	events: EventEntry[];
	universe: string[];
}

// ---- Backtesting (additive; replays the live engine over a date range) ------

export type BacktestOutcome = 'target' | 'stop' | 'timeout' | 'open';

/** A signal produced on a specific historical day, with its simulated outcome. */
export interface BacktestSignal {
	date: string; // ISO date the signal fired
	symbol: string;
	direction: Direction;
	score: number;
	confidence: number;
	positionSize: number;
	stopDistance: number;
	targetDistance: number;
	regime: RegimeName;
	approved: boolean;
	price: number; // entry (close on the signal date)
	outcome: BacktestOutcome;
	realizedReturn: number; // direction-adjusted fraction (+ = profit)
	exitDate: string | null;
	holdDays: number;
}

export interface BacktestSummary {
	from: string;
	to: string;
	tradingDays: number;
	proposals: number; // directional signals evaluated
	approved: number; // cleared the risk firewall (incl. re-signals)
	entered: number; // actual trades taken (one per symbol until it exits)
	closed: number; // entered trades with a realized outcome
	wins: number;
	losses: number;
	winRate: number; // [0,1] over closed trades
	avgReturn: number; // mean realized return per closed trade (fraction)
	expectancy: number; // size-weighted mean realized return
	totalReturn: number; // compounded size-weighted equity (fraction)
	maxDrawdown: number; // on the equity curve (fraction, <= 0)
	bestTrade: number;
	worstTrade: number;
	avgHoldDays: number;
}

export interface EquityPoint {
	date: string;
	equity: number; // starts at 1.0
}

export interface RegimePoint {
	date: string;
	regime: RegimeName;
	confidence: number;
}

export interface BacktestResult {
	summary: BacktestSummary;
	signals: BacktestSignal[]; // approved directional signals (most recent first)
	equityCurve: EquityPoint[];
	regimeTimeline: RegimePoint[];
	dataSource: DataSource;
	symbolFilter: string | null;
	truncated: boolean; // true if the signals list was capped
}
