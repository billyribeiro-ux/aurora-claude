# AURORA — 24/7 Autonomous Operation Runbook

*The continual-learning loop: what runs, when, and how to arm it durably.*

## The nightly cycle (what "24/7" actually does)

Every weekday evening after US market close, the autonomous cycle:

1. **Refreshes data** — `12_learned_pipeline/refresh.py` appends the latest EOD
   bars to every cached symbol (732 names incl. delisted). Honest failure
   semantics: exit `2` = no API key, exit `3` = provider rate-limited — the
   cycle stops rather than run research on data it could not refresh.
2. **Re-runs the evidence** — the survivorship-free certification
   (`13_certification/certify_pit.py`, gates L1/L3/L4/L5/L6 incl. PBO and the
   Deflated Sharpe Ratio) and the multi-year walk-forward
   (`14_alpha_research/walkforward.py`).
3. **Commits only what changed** — if a gate verdict or headline number moved,
   `RESULTS.md` is updated and pushed; otherwise nothing is committed.
4. **Reports one line** — rows added, gates changed/unchanged, edge verdict.

Run it manually any time:

```bash
cd 12_learned_pipeline && python3 refresh.py            # exit 0 ok / 2 no key / 3 throttled
cd ../13_certification && python3 certify_pit.py
cd ../14_alpha_research && python3 walkforward.py
```

## Arming it durably (one-time, needs an interactive session)

The scheduler that survives container restarts is a **claude.ai Routine**
(server-side trigger). Creating it requires a tool-permission approval that a
non-interactive session cannot grant — in this session, every attempt aborted
the permission stream. To arm it:

1. Open this session (or a new one on this repo) **interactively** on
   claude.ai/code.
2. Ask: *"Create a Routine named 'AURORA nightly continual-learning cycle',
   cron `30 22 * * 1-5`, that runs the nightly cycle in
   `00_architecture/runbook_24x7.md` step by step."*
3. Approve the permission prompt when it appears. Done — it fires every
   weekday at 22:30 UTC regardless of container lifecycle.

For fully headless fresh-session firing, also add `FMP_API_KEY` to the
environment's variables in the Claude Code environment settings — `frontend/.env`
is gitignored and does not exist in fresh clones.

## Failure policy (unchanged from the north star)

- Never report refreshed-looking results from stale data — refresh failures stop
  the cycle loudly.
- Never commit unchanged evidence — a quiet night produces no commits.
- Never fabricate: every number in `RESULTS.md` traces to an artifact produced
  by a reproducible script.
