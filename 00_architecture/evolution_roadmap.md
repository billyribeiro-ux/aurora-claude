# AURORA-SWING — Evolution Roadmap

*From a transparent heuristic engine to an autonomous, learning AI quant
organization — without ever compromising the safety and evidence guarantees
that already hold today.*

This document scopes the path forward. It is deliberately incremental: every
stage ships behind the **existing risk firewall**, is gated on **hard evidence**
(the same standard the current system is held to), and is **additive** — it must
never silently change the behaviour of the live decision path that is validated
today.

---

## 0. Where we are today (the baseline that must not regress)

The platform is already end-to-end and provably honest about its own data:

| Capability | Status | Evidence |
| ---------- | ------ | -------- |
| Data layer (01) → training scaffolds (09) | Built, typed, tested | `pytest tests/` (24 passing) |
| Deployment engine (10) | Built | `AuroraLiveEngine`, `SignalGenerator`, `ModelMonitor` |
| Live console (SvelteKit, strict TS) | Built | `frontend/` — 7 pages, e2e smoke suite |
| Live market data (FMP, server-side) | Verified live | 120/120 exact OHLC match vs raw provider |
| Backtest with no look-ahead leakage | Verified | `e2e/integrity.spec.ts` — reproducible + leakage-free |
| Multi-agent research committee scaffold (11) | Scaffolded | `tests/test_research_agents.py` (5 passing) |

**Two properties are non-negotiable and already proven, and every future stage
inherits them:**

1. **No look-ahead leakage.** A decision for day *D* is a pure function of bars
   with index ≤ *D*. Adding future data never changes a past decision. This is
   an integration test, not a comment.
2. **Honest provenance.** Data is labelled `FMP` only when it genuinely came
   from the live provider; any fallback is labelled `SYNTHETIC`. Nothing
   downstream is allowed to mistake a fallback for real data.

The current decision engine is a **transparent heuristic** (regime detection +
rule-based signal scoring). It is deliberately simple and auditable. The
roadmap replaces its *internals* with learned components **one at a time**,
keeping the same `TradingSignal` contract and the same risk firewall so each
swap is measurable in isolation.

---

## 1. Guiding principles for the evolution

**P1 — The contract is the firewall.** Every new component (learned model,
agent, ensemble) emits the exact same `TradingSignal` shape and passes through
the exact same risk engine. We never widen the blast radius to add capability.

**P2 — Shadow before authority.** A new component runs in *shadow mode* first:
it produces signals that are logged and scored against the incumbent, but do
**not** move capital. It earns authority only by beating the incumbent on
out-of-sample, walk-forward evidence.

**P3 — Every promotion is gated on hard evidence.** No component is promoted on
a backtest alone. Promotion requires: (a) walk-forward out-of-sample results,
(b) leakage tests still green, (c) a paper-trading period, (d) a documented
kill switch.

**P4 — Additive, always.** New modules live in new directories and new
server modules. The validated live path is modified only when a promotion has
cleared every gate — and even then, the previous path stays runnable behind a
flag for instant rollback.

**P5 — Reproducibility is a feature.** Given identical inputs, the system
produces identical outputs. Determinism is what makes evidence trustworthy;
we keep it (seeded RNG, pinned data snapshots, versioned model artifacts).

---

## 2. The two evolution tracks

The vision has two tracks that converge. They can be developed in parallel
because they meet only at the signal contract.

```
        TRACK A — LEARNED DECISION STACK          TRACK B — RESEARCH ORGANIZATION
        (replace the engine internals)            (replace the analyst desk)

        heuristic engine  ── shadow ──►           committee scaffold (Module 11)
              │            trained models                   │
              ▼                                             ▼
        foundation encoder                        specialist agents (macro,
              │                                    technical, risk, ... )
              ▼                                             │
        world model (futures + σ)                          ▼
              │                                    debate / aggregation
              ▼                                             │
        RL policy (entries/size/exits)                      ▼
              │                                    advisory conviction
              └───────────────┬────────────────────────────┘
                              ▼
                     SAME TradingSignal contract
                              ▼
                     RISK FIREWALL (unchanged)
                              ▼
                     EXECUTION / PAPER / LIVE
```

### Track A — the learned decision stack

Replace the heuristic scorer's internals with the model stack from
`system_design.md`, in dependency order, each behind a shadow gate:

1. **Foundation encoder** (self-supervised market representation). Deliverable:
   latent vectors per symbol/day. Gate: representations improve a *frozen* linear
   probe on regime/return-sign versus hand-built features, out-of-sample.
2. **World model** (latent dynamics → future distribution + uncertainty).
   Deliverable: calibrated N-day return distributions. Gate: proper scoring
   rule (CRPS / log-loss) beats a naive volatility model on held-out windows.
3. **RL policy** (entries, sizing, exits, stops, holding). Deliverable: a policy
   that consumes latent state + world-model rollouts. Gate: walk-forward
   risk-adjusted return beats the heuristic engine *after* the risk firewall,
   with equal or lower drawdown.
4. **Continual learning loop** (record → evaluate → detect failure → update
   selectively). Gate: updates are staged and A/B'd; a regression auto-reverts.

Each stage is a *drop-in* behind the signal contract. If stage *k* fails its
gate, the system keeps running stage *k−1*. There is no "big bang" cutover.

### Track B — the autonomous research organization

Grow Module 11 (`11_research_agents/`) from a scaffold into a standing research
desk that produces an **advisory conviction** feeding the same firewall.

Current scaffold (built): `Stance`, `AgentOpinion`, `ResearchAgent` protocol,
`MacroAgent` / `TechnicalAgent` / `RiskAnalystAgent`, and a weighted
`ResearchCommittee` that aggregates signed conviction + consensus into a
`CommitteeDecision`.

Growth path:

1. **More specialists** — flow/positioning, credit/rates, cross-asset,
   event/catalyst, sentiment. Each is a small, independently testable
   `ResearchAgent`.
2. **Structured debate** — agents see each other's opinions and revise (a
   bounded, deterministic round), surfacing disagreement instead of averaging
   it away. Disagreement is signal.
3. **Evidence memory** — every committee call is logged with the context and
   the eventual outcome, so agent weights become *earned* (track-record
   weighting) rather than hand-set.
4. **Advisory only, then gated authority** — the committee's conviction first
   only *annotates* signals (shadow); it earns the right to *veto* or *scale*
   a signal only after its track record clears the same evidence gates as
   Track A. It never bypasses the risk firewall.

---

## 3. Phased delivery plan

| Phase | Goal | Exit gate (hard evidence) |
| ----- | ---- | ------------------------- |
| **E0 — Foundations** *(done)* | Live data, backtest, no-leakage tests, committee scaffold | 120/120 data match; leakage tests green; 24 pytest + e2e passing |
| **E1 — Evidence harness** | Walk-forward + shadow-scoring infra; every component scored the same way | Walk-forward report reproducible; shadow log for ≥1 component |
| **E2 — Representation** | Foundation encoder in shadow | Linear-probe beats hand features OOS |
| **E3 — Forecasting** | World model in shadow | Calibrated distribution beats naive baseline OOS |
| **E4 — Policy** | RL policy in shadow, then gated authority on paper | Walk-forward risk-adjusted return ≥ heuristic, drawdown ≤ heuristic |
| **E5 — Research desk** | Module 11 committee to advisory-live, then gated authority | Track-record-weighted committee improves paper expectancy |
| **E6 — Continual loop** | Online evaluation + selective, auto-reverting updates | A regression auto-reverts within one evaluation cycle |

Phases are ordered by dependency, not calendar. E1 (the evidence harness) is
the highest-leverage next step: it is what lets every later phase be judged
honestly, and it reuses the leakage/reproducibility guarantees already proven.

---

## 4. Safety & governance (unchanged authority model)

The safety rules from `system_design.md` and `operating_protocol.md` remain the
supreme law. Restated for the autonomous era:

- **The risk firewall has final authority.** No learned model, no agent, no
  committee can bypass position limits, exposure caps, drawdown limits, or the
  "don't trade in unknown states" rule.
- **Unknown state ⇒ no trade.** If regime confidence or model uncertainty is
  outside its validated envelope, the system stands down. Autonomy includes the
  autonomy to *not act*.
- **Every autonomous decision is attributable.** Which component/agent produced
  it, on what inputs, with what confidence — all logged. No black-box authority
  without an audit trail.
- **Kill switch per component.** Any promoted component can be demoted to shadow
  (or off) instantly via a flag, reverting to the last validated path.
- **Human-in-the-loop for capital-at-risk promotions.** Moving from paper to
  live capital is a gated, explicit action — never an automatic side effect of
  a model update.

---

## 5. Definition of done for "autonomous AI quant organization"

The vision is realised when **all** of the following hold simultaneously:

1. The decision stack is learned (foundation → world model → RL), each stage
   promoted only on out-of-sample evidence.
2. A standing research committee produces attributable, track-record-weighted
   convictions that measurably improve expectancy.
3. A continual-learning loop updates the system selectively and auto-reverts
   regressions.
4. The no-leakage and honest-provenance guarantees from E0 **still pass** — the
   same integration tests, still green.
5. The risk firewall has never been bypassed, and every capital-at-risk
   promotion was gated on paper-trading evidence and human sign-off.

Autonomy is earned capability under fixed safety — not removed safety.
