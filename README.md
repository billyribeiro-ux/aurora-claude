# AURORA-SWING

**A**utonomous **U**nified **R**einforcement & **O**ptimization **R**esearch
**A**rchitecture for **Swing** trading — a self-learning quantitative platform
for 3–20 day holding periods. It does not attempt deterministic price
prediction; it learns market-state representations, regimes, future probability
distributions and risk-adjusted decisions.

The repository contains the Python research modules (built out module-by-module)
and the **AURORA-SWING Console** (`frontend/`): a state-of-the-art SvelteKit
dashboard (Svelte 5 + TypeScript strict) for monitoring the live decision
pipeline, signals, markets, health and architecture.

> **Read [`RESULTS.md`](RESULTS.md) first.** It is the honest evidence ledger.
> AURORA is a **research platform** and makes **no claim of a profitable edge** —
> in fact it *proves*, survivorship-free, that the current signal has none. The
> value is the rigor: survivorship-free point-in-time testing, PBO, embargoed
> walk-forward, leakage-controlled data, and results reported as-measured. See
> also [`00_architecture/north_star.md`](00_architecture/north_star.md).

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
├── 00_architecture/            # system_design.md — the canonical design document
├── 01_data/                    # schema, feature engineering, timeframe sync, pipeline
├── 02_foundation_model/        # embeddings, transformer encoder, world model, losses, pretraining
├── 03_regime_engine/           # latent GMM + HMM + ensemble regime manager
├── 04_environment/             # transaction costs, portfolio, execution sim, Gym env
├── 05_risk_engine/             # volatility model, position sizing, gap risk, risk firewall
├── 06_reinforcement_learning/  # actor/critic, PPO, SAC, prioritized replay, reward
├── 07_continual_learning/      # experience DB, drift detection, EWC, model-update gate
├── 08_backtesting/             # walk-forward, Monte Carlo, evaluation metrics
├── 09_training/                # foundation / world-model / RL trainers + master pipeline
├── 10_deployment/              # AuroraLiveEngine, SignalGenerator, ModelMonitor (+ tests)
├── 11_research_agents/         # multi-agent research committee scaffold
├── 12_learned_pipeline/        # trained self-supervised encoder + honest OOS harness
├── 13_certification/           # institutional L1–L6 gauntlet incl. survivorship-free PIT
├── 14_alpha_research/          # rich features + cross-sectional rank-normalization
├── 15_fundamentals/            # leakage-safe point-in-time fundamental factors
├── tests/                      # pytest suite (47 tests)
├── RESULTS.md                  # ← the honest evidence ledger
├── requirements.txt            # Python dependencies
└── frontend/                   # AURORA-SWING Console (SvelteKit)
    └── src/
        ├── lib/server/         #   FMP client + decision engine (server-only)
        ├── lib/components/     #   design-system components
        └── routes/             #   Command Center, Signals, Markets,
                                #   Monitoring, Architecture, Protocol
```

> Modules 00–15 are implemented. The architecture modules (01–09) use dependency
> injection so they integrate without hard coupling; 10 deploys; 12–15 are the
> **evidence layer** — actually-trained models and the certification harness that
> holds every claim to survivorship-free, out-of-sample, PBO-checked proof. Every
> module is typed, documented, `__all__`-scoped and tested.

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
