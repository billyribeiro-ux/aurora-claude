# Module 10 — Production Deployment Engine

The layer that turns **AURORA-SWING** from a research system into an operating
autonomous quant platform.

## Responsibilities

1. **Load trained models** — injected into `AuroraLiveEngine` (no hard-coded
   coupling to upstream modules).
2. **Process live market state** — `AuroraLiveEngine.analyze_market`.
3. **Generate decisions** — `SignalGenerator.generate` → `TradingSignal`.
4. **Monitor system health** — `ModelMonitor.check_health`.

## Design principle

The live system **never** trades directly from the neural-network output.
Every proposed action must clear the risk firewall first:

```
LIVE MARKET DATA
      │
      ▼
Foundation Encoder      →  latent market intelligence
      │
      ▼
World Model Forecast    →  future latent + uncertainty
      │
      ▼
Regime Detection        →  operating environment
      │
      ▼
RL Decision             →  raw action proposal
      │
      ▼
Risk Firewall           →  approve / reject / resize
      │
      ▼
Execution Layer
      │
      ▼
Trade
```

## Files

| File                 | Purpose                                                        |
| -------------------- | ------------------------------------------------------------- |
| `live_engine.py`     | Main inference engine — orchestrates the full pipeline.       |
| `signal_service.py`  | Turns an analysis record into a structured `TradingSignal`.   |
| `monitoring.py`      | Autonomous self-monitoring and health alerts.                 |
| `__init__.py`        | Public package surface.                                       |

## Usage

```python
from importlib import import_module

deployment = import_module("10_deployment")  # leading digit → import via importlib

engine = deployment.AuroraLiveEngine(
    encoder=encoder,
    world_model=world_model,
    regime_engine=regime_engine,
    policy=policy,
    risk_manager=risk_manager,
)

analysis = engine.analyze_market(market_tensor, regime_features, portfolio)

signal = deployment.SignalGenerator().generate("NVDA", analysis)
if signal.approved:
    execution_layer.submit(signal)

monitor = deployment.ModelMonitor()
alerts = monitor.check_health({
    "drawdown": 0.08,
    "uncertainty": 0.42,
    "reward_decay": 0.05,
})
```

> **Note on the directory name.** Like the rest of the AURORA-SWING repo, this
> package is prefixed with a number for ordering. Python cannot `import
> 10_deployment` directly (identifiers may not start with a digit), so load it
> via `importlib.import_module("10_deployment")`. Relative imports inside the
> package work normally once it is loaded.

## Dependencies

See [`requirements.txt`](./requirements.txt). `torch` is required by the
inference engine; `signal_service` and `monitoring` are pure-Python and have no
third-party dependencies.
