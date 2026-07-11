/**
 * Server-side runtime configuration — SERVER ONLY.
 *
 * Reads dynamic (runtime) env vars so the operator can change mode / universe
 * without a rebuild.
 */

import { env } from '$env/dynamic/private';
import type { SystemMode } from '$lib/types';
import { symbolsFromEnv } from '$lib/universe';

export function getMode(): SystemMode {
	const raw = (env.AURORA_MODE ?? 'PAPER').toUpperCase();
	if (raw === 'LIVE' || raw === 'PAPER' || raw === 'DEMO') return raw;
	return 'PAPER';
}

export function getUniverse(): string[] {
	return symbolsFromEnv(env.AURORA_UNIVERSE);
}
