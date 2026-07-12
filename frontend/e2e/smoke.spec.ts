import { test, expect } from '@playwright/test';

const routes = ['/', '/signals', '/markets', '/backtest', '/monitoring', '/architecture', '/protocol', '/research'];

for (const path of routes) {
	test(`page loads: ${path}`, async ({ page }) => {
		const res = await page.goto(path);
		expect(res?.status(), `HTTP status for ${path}`).toBeLessThan(400);
		await expect(page.locator('h1').first()).toBeVisible();
	});
}

test('home page has no console errors (guards favicon / asset 404s)', async ({ page }) => {
	const errors: string[] = [];
	page.on('console', (m) => {
		if (m.type() === 'error') errors.push(m.text());
	});
	page.on('pageerror', (e) => errors.push(e.message));
	await page.goto('/');
	await page.waitForLoadState('networkidle');
	expect(errors, errors.join('\n')).toHaveLength(0);
});

test('command center: live toggle flips state', async ({ page }) => {
	await page.goto('/');
	const btn = page.locator('button.live');
	await expect(btn).toBeVisible();
	const before = (await btn.innerText()).trim();
	await btn.click();
	await expect(btn).not.toHaveText(before);
});

test('markets: selecting a watchlist symbol updates the chart', async ({ page }) => {
	await page.goto('/markets');
	await page.locator('.quote:has(.sym:text-is("NVDA"))').click();
	await expect(page.locator('.chart-card h3')).toHaveText('NVDA');
});

test('backtest: runs and populates the signals ledger', async ({ page }) => {
	await page.goto('/backtest');
	const [from, to] = await page.locator('input[type="date"]').all();
	await from.fill('2026-01-05');
	await to.fill('2026-05-01');
	const resp = page.waitForResponse((r) => r.url().includes('/api/backtest'));
	await page.getByRole('button', { name: /run backtest/i }).click();
	await resp;
	await expect(page.locator('.table-wrap tbody tr').first()).toBeVisible({ timeout: 30_000 });
});

test('backtest: Run is disabled for an invalid (from > to) range', async ({ page }) => {
	await page.goto('/backtest');
	const [from, to] = await page.locator('input[type="date"]').all();
	await from.fill('2026-06-01');
	await to.fill('2026-05-01');
	await expect(page.getByRole('button', { name: /run backtest/i })).toBeDisabled();
});
