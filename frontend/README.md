# AURORA-SWING Console

A trading-terminal dashboard for the AURORA-SWING autonomous quant platform,
built with **SvelteKit + Svelte 5 (runes) + TypeScript (strict mode)**.

## What it shows

| Route         | Content                                                                   |
| ------------- | ------------------------------------------------------------------------- |
| `/`           | **Command Center** — KPIs, the inference pipeline, regime, health, live signals, event stream. Polls every 20s. |
| `/signals`    | Full decision ledger with the risk-firewall trail for each proposal.      |
| `/markets`    | Grouped watchlist (market / macro / sectors / equities) + interactive price chart. |
| `/monitoring` | System health, model drift and the weekly continual-improvement loop.     |
| `/protocol`   | Training sequence, 7-level validation framework and honest assessment.    |

## Running

```bash
npm install
cp .env.example .env      # paste your FMP_API_KEY
npm run dev               # http://localhost:5173
```

Production (standalone Node server via `adapter-node`):

```bash
npm run build
FMP_API_KEY=your_key node build
```

## How data flows

- **`src/lib/server/fmp.ts`** — the Financial Modeling Prep client. It lives
  under `$lib/server`, so SvelteKit guarantees it can never reach the browser.
  The key is read at runtime from `$env/dynamic/private` (`process.env`), so you
  can supply it after deployment with no rebuild. No key → synthetic fallback.
- **`src/lib/server/aurora.ts`** — the decision engine: regime detection, signal
  generation, the risk firewall and health monitoring. Emits the same
  `TradingSignal` / regime / health contract as the Python deployment layer.
- **`src/routes/api/*`** — server endpoints (`/api/status`, `/api/history`) that
  return computed, key-free JSON for client-side polling and charting.

## Quality gates

```bash
npm run check     # svelte-check — TypeScript strict + Svelte validation (0/0)
npm run build     # production build
```

Every Svelte component was validated with the official Svelte MCP autofixer.
