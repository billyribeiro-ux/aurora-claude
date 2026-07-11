# AURORA-SWING

**A**utonomous **U**nified **R**einforcement & **O**ptimization **R**esearch
**A**rchitecture for **Swing** Trading.

## Mission

AURORA-SWING is a self-learning quantitative swing-trading platform designed for
**3–20 trading-day** holding periods.

The system does **not** attempt deterministic price prediction. Instead it
learns:

- Market state representations
- Market regimes
- Future probability distributions
- Risk-adjusted trading decisions

---

## Core Architecture

```
                 MARKET DATA
                     |
                     v
          DATA NORMALIZATION LAYER
                     |
                     v
      MULTI-TIMEFRAME MARKET ENCODER
                     |
                     v
          LATENT MARKET STATE
                     |
    --------------------------------
    |                              |
    v                              v
 WORLD MODEL                  REGIME ENGINE
    |                              |
    --------------------------------
                     |
                     v
           RL DECISION ENGINE
                     |
                     v
             RISK FIREWALL
                     |
                     v
              EXECUTION ENGINE
                     |
                     v
         CONTINUAL LEARNING LOOP
```

---

## Design Principles

**1. Representation before prediction.** The system first learns what market
conditions *mean*. Trading decisions are made only after understanding the
latent environment.

**2. Risk has authority.** The reinforcement-learning agent cannot bypass
portfolio protection. Risk management operates independently and can override
any decision.

**3. Continual improvement.** The system continuously records experiences,
evaluates decisions, detects failures and updates *selectively* — never blindly.

---

## Model Stack

| Component          | Purpose                                   | Technology                                             |
| ------------------ | ----------------------------------------- | ------------------------------------------------------ |
| **Foundation**     | Learn generalised market representations  | PyTorch transformer encoder, self-supervised           |
| **World Model**    | Generate possible future trajectories     | Latent dynamics → future states, expected reward, σ    |
| **RL Agent**       | Entries, sizing, exits, stops, holding    | Hybrid PPO + SAC                                        |
| **Regime Engine**  | Classify the market environment           | HMM + volatility clustering + latent GMM + neural head |
| **Risk Engine**    | Sizing, exposure, volatility, drawdown, correlation, gap | Independent firewall                    |

Foundation objectives: masked market reconstruction, contrastive learning,
latent future prediction. The world model's outputs (future latent states,
expected rewards, uncertainty) are used for planning, scenario analysis and risk
adjustment.

---

## Trading Lifecycle

1. Market-data ingestion
2. Feature generation
3. Latent representation generation
4. World-model simulation
5. Regime classification
6. RL decision generation
7. Risk approval
8. Execution simulation
9. Experience logging
10. Continual improvement

## Training Pipeline

1. Foundation-model pretraining
2. World-model training
3. Simulator validation
4. RL training
5. Walk-forward testing
6. Paper trading
7. Controlled deployment

---

## Non-Negotiable Safety Rules

The system must **never**:

- exceed portfolio risk limits
- trade during unknown model states
- bypass risk controls
- train on future information
- use future labels
- optimise only historical returns

## Production Philosophy

AURORA-SWING is treated as an autonomous research scientist. It generates
hypotheses, tests them, measures evidence, and adapts **only when statistical
proof exists**.

---

# SECTION 1 — DETAILED ARCHITECTURE

## 1.1 High-Level System Diagram

```
                         MARKET DATA UNIVERSE
                                 |
        ------------------------------------------------
        |                       |                       |
        v                       v                       v
   Price Data              Macro Data            Alternative Data
   OHLCV                   VIX Complex           Sentiment
   Daily / 4H / 1H         Rates / Dollar        Earnings
                           Breadth               Fundamentals / Analyst
        |                       |                       |
        ------------------------------------------------
                                |
                                v
        MULTI-TIMEFRAME MARKET FOUNDATION MODEL
        Raw sequence -> Hierarchical Transformer Encoder
            -> Short-Term Latent (4H/1H) + Long-Term Latent (Daily/Weekly)
            -> LATENT MARKET REPRESENTATION  z(t)
                                |
                                v
              SELF-SUPERVISED WORLD MODEL
        z(t) -> Latent Dynamics -> z(t+1), z(t+5), z(t+20)
            -> Future Scenario Simulator
               A: Bull continuation   B: Mean reversion
               C: Breakdown           D: Volatility expansion
                                |
                                v
                 REGIME INTELLIGENCE ENGINE
        Hybrid Detector = HMM State Model + Neural Clustering
        Regimes: Strong Bull | High-Vol Rotation | Bear |
                 Mean Reversion | Liquidity Shock
                                |
                                v
                  RL DECISION ENGINE (PPO + SAC)
        State = [latent, regime, portfolio, risk, world_predictions]
        Actions = Entry + Size + Stop + Target + Trail + Exit
                                |
                                v
                    RISK FIREWALL  (overrides the AI)
        Max Drawdown, Portfolio Heat, Correlation, Sector,
        Volatility, Gap, Liquidity, Earnings
                                |
                                v
              EXECUTION ENGINE  (Paper -> Live)
                                |
                                v
                CONTINUAL LEARNING LOOP
        Outcome -> Experience DB -> Priority Replay + Error Analysis
            -> Selective Model Updates -> Improved Understanding
```

## 1.2 The Five Intelligence Layers

### Layer 1 — Market Perception

Equivalent to human vision. The model does not see *"Apple price went up."* It
sees a **market state vector**:

```
Trend: +0.82   Momentum: +0.61   Volatility: Increasing
Liquidity: Normal   Breadth: Weakening   Institutional Flow: Accumulating
Regime Probability: Bull Trend 72% | Distribution 18% | Reversal 10%
```

### Layer 2 — Market World Model

The most important component. Rather than *"Will tomorrow go up?"* it asks
*"If current conditions continue, what are the possible futures?"*

```
Continuation:      p = 48%   E[return] = +4.2%
Pullback:          p = 37%   E[return] = -2.1%
Volatility Event:  p = 15%   E[return] = -5.8%
```

### Layer 3 — Regime Intelligence

*"What game are we currently playing?"*

| Regime         | Characteristics                                      | Behavior                                        |
| -------------- | ---------------------------------------------------- | ----------------------------------------------- |
| Momentum       | Trending sectors, expanding breadth, low correlation | Hold winners longer, wider stops, larger sizing |
| Mean Reversion | Range-bound, failed breakouts, oscillation           | Smaller positions, faster exits, tight targets  |
| Crisis         | VIX spike, correlation explosion, gap risk           | Reduce exposure, increase cash, disable entries |

### Layer 4 — RL Decision System

Learns *"What action maximizes risk-adjusted long-term capital growth?"*

```
ENTER_LONG / ENTER_SHORT
POSITION_SIZE: 0% | 10% | 25% | 50% | 75% | 100%
STOP:   1 ATR | 1.5 ATR | 2 ATR | 3 ATR
TARGET: 1R | 2R | 3R | Dynamic
TRAIL:  NONE | ATR TRAIL | STRUCTURAL TRAIL
EXIT:   HOLD | REDUCE | CLOSE
```

### Layer 5 — Autonomous Improvement

Evaluates *Was my decision correct? Was my reasoning correct? Did the regime
change? Did my model misunderstand something? Did risk management save me?* —
then stores experience, identifies errors and updates **selectively**.

## 1.3 Why This Architecture Is Superior

Most retail AI systems: `Price → Indicators → Neural Network → Buy/Sell`. This
fails — markets change, features decay, overfitting occurs, no risk intelligence
exists.

AURORA-SWING: `Market Data → Representation Learning → Market Understanding →
Scenario Simulation → Regime Awareness → Risk-Constrained Decision → Continuous
Learning` — closer to how autonomous systems are built in robotics, aerospace
and advanced AI research.

---

# SECTION 2 — DETAILED TECHNICAL SPECIFICATIONS

## 2.1 Self-Supervised Market Foundation Model

**Objective.** A general-purpose latent representation model `z_t =
Encoder(X_{t-k:t})`, where `X` = multi-timeframe market observations and `z_t` =
learned market state vector. It learns trend structure, volatility regime,
liquidity, momentum persistence, reversal patterns, cross-asset relationships and
microstructure proxies. The model should **not** know the trading objective
initially — this prevents the RL stage from overfitting the representation.

## 2.2 Input Representation

```
Daily  : [open, high, low, close, volume, ATR, RSI, MACD, ADX,
          VWAP-distance, relative-strength, volatility, sector-strength]
4H     : [OHLCV, momentum, trend, volume-anomalies]
Context: [SPY, QQQ, IWM, VIX, DXY, TNX, sector ETFs]
```

Final feature tensor `X_t ∈ R^{N × F}`, e.g. `N = 256` candles, `F = 96`.

## 2.3 Hierarchical Transformer Encoder

```
Input -> Patch Embedding -> Local Transformer -> Temporal Compression
      -> Global Transformer -> Latent Market State
```

| Encoder | Layers | Embedding | Heads | FFN  | Dropout | Activation |
| ------- | ------ | --------- | ----- | ---- | ------- | ---------- |
| Local   | 6      | 256       | 8     | 1024 | 0.1     | GELU       |
| Global  | 8      | 512       | 16    | 2048 | 0.15    | —          |

Attention: `softmax(QKᵀ / √d) V`.

## 2.4 Self-Supervised Objectives

- **Masked Market Modeling** (BERT-style): mask candles/features/segments,
  reconstruct. `L_mask = MSE(X, X̂)`.
- **Contrastive Learning**: similar environments → similar latents. NT-Xent,
  `L_c = -log[ exp(sim(z_i,z_j)/τ) / Σ_k exp(sim(z_i,z_k)/τ) ]`, `τ = 0.07`.
- **Predictive Latent Modeling**: predict `z_{t+1}`, `z_{t+20}`.
  `L_p = ||z_future − ẑ_future||²`.

**Combined:** `L = 0.4·L_mask + 0.3·L_contrastive + 0.3·L_predictive`.

**Training:** AdamW · LR 3e-4 · weight-decay 0.01 · batch 256 · 200–500 epochs ·
cosine decay · 10-epoch warmup · bf16.

## 2.5 Latent World Model

Inspired by MuZero and DreamerV3. Input `z_t`, output `(z_{t+1}, …, z_{t+n})`.
Dynamics: transformer decoder, 12 layers, embedding 512, 16 heads, context 128.
Outputs future state `ẑ_{t+k}`, expected reward `r̂` and **uncertainty `σ`** —
the system knows when it is confused.

## 2.6 World Model Training

`L_world = L_z + 0.5·L_r + 0.2·L_uncertainty`, where `L_z = MSE(z, ẑ)`,
`L_r = MSE(r, r̂)`, `L_u = KL(P || Q)`.

## 2.7 RL Decision Engine

Hybrid PPO (stability) + SAC (exploration). State ≈ 1024–2048 features.

Continuous actions: `position_size 0→1`, `stop_distance 0.5→5 ATR`,
`profit_target 0.5→8 R`, `trail_strength 0→1`, `hold_probability 0→1`.

PPO: clip 0.2 · gamma 0.995 · lambda 0.95 · epochs 10 · batch 4096 · entropy
0.01 · LR 3e-5.

## 2.8 Reward Function

```
R = P − D − G − T − E
P = log(Portfolio_t / Portfolio_{t-1})   # profit
D = 5 · maxDD                            # drawdown penalty
G = 2 · GapRisk                          # gap penalty
T = 0.001 · daysHeld                     # time decay
E = ExposureViolation                    # excess-risk penalty
```

## 2.9 Regime Detection

Three-layer ensemble: **HMM** (Bull/Bear/Range/High-Vol/Crisis) + **latent
clustering** (GMM + HDBSCAN) + **neural classifier** (`P(Regime_i)`). Final =
`40% HMM + 40% latent clustering + 20% neural`.

## 2.10 Risk Engine

Independent. The AI requests (e.g. `BUY, 75%, 2 ATR stop`); the engine returns
`APPROVED | MODIFIED | DENIED`.

| Control              | Limit                                              |
| -------------------- | -------------------------------------------------- |
| Portfolio heat       | 5% total capital at risk                           |
| Single position      | 2%                                                 |
| Sector exposure      | 20%                                                |
| Correlation          | Reduce size if correlation > 0.85 between holdings |
| Volatility targeting | 15% annualized — `Size = TargetVol / CurrentVol`   |

Overnight gap model: `E(Gap) = f(ATR, VIX, EventRisk)`.
