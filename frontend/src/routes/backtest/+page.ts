import type { PageLoad } from './$types';

export const load: PageLoad = () => {
	const to = new Date();
	const from = new Date(to.getTime() - 90 * 86_400_000);
	return {
		pageTitle: 'Backtest',
		pageSubtitle: 'Replay the decision engine over a date range',
		defaultFrom: from.toISOString().slice(0, 10),
		defaultTo: to.toISOString().slice(0, 10)
	};
};
