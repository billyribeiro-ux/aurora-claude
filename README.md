# AURORA-SWING

An autonomous, adaptive quant research & trading platform. This repository
delivers two things:

1. **Module 10 — Production Deployment Engine** (`10_deployment/`): the Python
   inference layer that turns AURORA-SWING from a research system into an
   operating platform.
2. **AURORA-SWING Console** (`frontend/`): a state-of-the-art SvelteKit
   dashboard (Svelte 5 + TypeScript strict) for monitoring the live decision
   pipeline, signals, markets and system health.

## The decision flow

The live system **never** trades directly from the neural-network output.
Every proposed action must clear the risk firewall first:

```
LIVE MARKET DATA → Foundation Encoder → World Model → Regime Engine
        → RL Policy → Risk Firewall → Execution → Trade
```

## Repository layout

```
aurora-claude/
├── 10_deployment/          # Module 10 — Python deployment engine
│   ├── live_engine.py      #   AuroraLiveEngine — orchestrates the pipeline
│   ├── signal_service.py   #   SignalGenerator → TradingSignal
│   ├── monitoring.py       #   ModelMonitor — self-health & alerts
│   ├── tests/              #   unit tests (pure-Python parts run without torch)
│   └── requirements.txt
└── frontend/               # AURORA-SWING Console (SvelteKit)
    └── src/
        ├── lib/server/     #   FMP client + decision engine (server-only)
        ├── lib/components/  #   design-system components
        └── routes/         #   Command Center, Signals, Markets, Monitoring, Protocol
```

## Backend — Module 10

The deployment engine uses **dependency injection**: the encoder, world model,
regime engine, policy and risk manager are passed into `AuroraLiveEngine`, so it
has no hard coupling to any upstream module. See
[`10_deployment/README.md`](10_deployment/README.md).

```bash
# Run the tests (torch-free parts run anywhere; the full pipeline test
# runs when torch is installed).
python3 -m unittest discover -s 10_deployment/tests -v
```

## Frontend — the Console

A SvelteKit app that renders the live pipeline. It reads market data from
**Financial Modeling Prep (FMP)** entirely server-side — the API key is never
shipped to the browser. Without a key it runs in a clearly-labelled *synthetic
data* mode so the UI is fully functional for review.

```bash
cd frontend
npm install
cp .env.example .env          # then paste your FMP_API_KEY
npm run dev                   # http://localhost:5173
```

Production:

```bash
cd frontend
npm run build
FMP_API_KEY=your_key node build   # standalone Node server (adapter-node)
```

### Configuration (`frontend/.env`)

| Variable          | Purpose                                              |
| ----------------- | ---------------------------------------------------- |
| `FMP_API_KEY`     | Financial Modeling Prep key (read server-side only). |
| `AURORA_MODE`     | `LIVE` · `PAPER` · `DEMO` — shown in the UI banner.  |
| `AURORA_UNIVERSE` | Optional comma-separated ticker override.            |

The console **derives its data source from what it actually fetched**: with a
valid key the header shows `LIVE DATA · FMP`; if the key is missing or the
provider is unreachable it falls back to synthetic data and says so.

## A note on scope

The console's decision engine (`frontend/src/lib/server/aurora.ts`) implements
the same decision *flow* as the trained pipeline — regime → signal → risk
firewall → health — using transparent, explainable analytics over live market
data. It emits the exact `TradingSignal` / regime / health contract that the
Python deployment layer produces, so the neural core (Modules 02–06) can be
swapped in behind the same API without changing the UI. See the **Protocol**
page in the app for the full training, validation and honest-assessment
framework.
