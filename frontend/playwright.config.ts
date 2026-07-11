import { defineConfig, devices } from '@playwright/test';

const PORT = 4319;

/**
 * E2E smoke config. Builds the app and serves it with adapter-node, then runs
 * the browser tests.
 *
 * - On CI / other machines: run `npx playwright install chromium` first.
 * - In this environment: the browser is pre-installed, so pass its path via
 *   `PW_CHROMIUM_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome`.
 * - Set `FMP_API_KEY` to smoke-test against live data (otherwise synthetic).
 */
export default defineConfig({
	testDir: './e2e',
	timeout: 45_000,
	fullyParallel: false,
	retries: 0,
	reporter: 'line',
	use: {
		baseURL: `http://127.0.0.1:${PORT}`,
		...(process.env.PW_CHROMIUM_PATH
			? { launchOptions: { executablePath: process.env.PW_CHROMIUM_PATH } }
			: {})
	},
	projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
	webServer: {
		command: 'npm run build && node build',
		port: PORT,
		timeout: 120_000,
		reuseExistingServer: !process.env.CI,
		env: {
			PORT: String(PORT),
			HOST: '127.0.0.1',
			AURORA_MODE: 'PAPER',
			FMP_API_KEY: process.env.FMP_API_KEY ?? ''
		}
	}
});
