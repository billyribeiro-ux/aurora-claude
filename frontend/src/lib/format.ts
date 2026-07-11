/** Formatting helpers shared across the console. Pure, no side effects. */

const nf = (min: number, max: number): Intl.NumberFormat =>
	new Intl.NumberFormat('en-US', { minimumFractionDigits: min, maximumFractionDigits: max });

/** Fixed-decimal number, e.g. 138.42. */
export function num(value: number, digits = 2): string {
	if (!Number.isFinite(value)) return '—';
	return nf(digits, digits).format(value);
}

/** USD currency. Large values are shown whole. */
export function currency(value: number, digits = 0): string {
	if (!Number.isFinite(value)) return '—';
	return `$${nf(digits, digits).format(value)}`;
}

/** A value that is ALREADY a percentage (e.g. 1.5 → "1.50%"). */
export function pct(value: number, digits = 2): string {
	if (!Number.isFinite(value)) return '—';
	return `${nf(digits, digits).format(value)}%`;
}

/** A fraction in [0,1] rendered as a percentage (e.g. 0.18 → "18.0%"). */
export function pctFrac(value: number, digits = 1): string {
	return pct(value * 100, digits);
}

/** Signed percentage from an already-percentage value (e.g. -1.2 → "−1.20%"). */
export function signedPct(value: number, digits = 2): string {
	if (!Number.isFinite(value)) return '—';
	const sign = value > 0 ? '+' : value < 0 ? '−' : '';
	return `${sign}${nf(digits, digits).format(Math.abs(value))}%`;
}

/** Signed number from a raw value. */
export function signed(value: number, digits = 2): string {
	if (!Number.isFinite(value)) return '—';
	const sign = value > 0 ? '+' : value < 0 ? '−' : '';
	return `${sign}${nf(digits, digits).format(Math.abs(value))}`;
}

/** Compact magnitude, e.g. 1.2B, 340M, 12.4K. */
export function compact(value: number | null): string {
	if (value === null || !Number.isFinite(value)) return '—';
	const abs = Math.abs(value);
	if (abs >= 1e12) return `${num(value / 1e12, 2)}T`;
	if (abs >= 1e9) return `${num(value / 1e9, 2)}B`;
	if (abs >= 1e6) return `${num(value / 1e6, 1)}M`;
	if (abs >= 1e3) return `${num(value / 1e3, 1)}K`;
	return num(value, 0);
}

/** HH:MM:SS in the viewer's locale. */
export function clock(iso: string): string {
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return '—';
	return d.toLocaleTimeString('en-US', { hour12: false });
}

/** Short date, e.g. "Jul 11". */
export function shortDate(iso: string): string {
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return '—';
	return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/** Relative time, e.g. "2m ago". */
export function relative(iso: string): string {
	const then = new Date(iso).getTime();
	if (Number.isNaN(then)) return '—';
	const secs = Math.round((Date.now() - then) / 1000);
	if (secs < 5) return 'just now';
	if (secs < 60) return `${secs}s ago`;
	const mins = Math.round(secs / 60);
	if (mins < 60) return `${mins}m ago`;
	const hrs = Math.round(mins / 60);
	if (hrs < 24) return `${hrs}h ago`;
	return `${Math.round(hrs / 24)}d ago`;
}

export function directionLabel(direction: number): string {
	if (direction > 0) return 'LONG';
	if (direction < 0) return 'SHORT';
	return 'FLAT';
}

export function regimeLabel(regime: string): string {
	return regime
		.split('_')
		.map((w) => w.charAt(0) + w.slice(1).toLowerCase())
		.join(' ');
}
