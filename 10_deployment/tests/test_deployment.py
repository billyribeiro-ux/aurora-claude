"""
Unit tests for Module 10 — Production Deployment Engine.

Runnable with either ``pytest`` or ``python -m unittest``. The signal-service
and monitoring tests are pure-Python. The full live-engine pipeline test only
runs when ``torch`` is installed; otherwise it is skipped so the suite stays
green in torch-free environments.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from datetime import datetime
from enum import Enum

# Load the sibling modules directly. The package directory starts with a digit
# ("10_deployment"), so we add it to sys.path and import the modules by name
# rather than using a normal `import 10_deployment` statement.
_MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

from monitoring import HealthThresholds, ModelMonitor  # noqa: E402
from signal_service import SignalGenerator, TradingSignal  # noqa: E402

_HAS_TORCH = importlib.util.find_spec("torch") is not None


class _Scalar:
    """Minimal stand-in for a 0-d tensor exposing ``.item()``."""

    def __init__(self, value: float) -> None:
        self._value = value

    def item(self) -> float:
        return self._value


class _Regime(Enum):
    BULL_TREND = 1
    CRISIS = 2


class SignalServiceTests(unittest.TestCase):
    def _analysis(self, *, uncertainty: float, approved: bool) -> dict:
        # raw_action = [direction, size, stop, target]
        action = [_Scalar(1), _Scalar(0.25), _Scalar(0.02), _Scalar(0.06)]
        return {
            "raw_action": action,
            "regime": {"regime": _Regime.BULL_TREND},
            "risk": {"approved": approved},
            "world": {"uncertainty": _Scalar(uncertainty)},
        }

    def test_generate_produces_trading_signal(self) -> None:
        signal = SignalGenerator().generate(
            "NVDA", self._analysis(uncertainty=0.3, approved=True)
        )
        self.assertIsInstance(signal, TradingSignal)
        self.assertEqual(signal.symbol, "NVDA")
        self.assertEqual(signal.direction, 1)
        self.assertAlmostEqual(signal.confidence, 0.7)
        self.assertAlmostEqual(signal.position_size, 0.25)
        self.assertEqual(signal.regime, "BULL_TREND")
        self.assertTrue(signal.approved)
        self.assertIsInstance(signal.timestamp, datetime)

    def test_confidence_is_clamped(self) -> None:
        # uncertainty > 1 would yield negative confidence without clamping.
        signal = SignalGenerator().generate(
            "AAPL", self._analysis(uncertainty=1.4, approved=False)
        )
        self.assertEqual(signal.confidence, 0.0)
        self.assertFalse(signal.approved)

    def test_to_dict_is_json_friendly(self) -> None:
        signal = SignalGenerator().generate(
            "MSFT", self._analysis(uncertainty=0.1, approved=True)
        )
        payload = signal.to_dict()
        self.assertIsInstance(payload["timestamp"], str)
        self.assertEqual(payload["regime"], "BULL_TREND")


class MonitoringTests(unittest.TestCase):
    def test_healthy_metrics_produce_no_alerts(self) -> None:
        monitor = ModelMonitor()
        alerts = monitor.check_health(
            {"drawdown": 0.05, "uncertainty": 0.4, "reward_decay": 0.05, "drift": 0.1}
        )
        self.assertEqual(alerts, [])

    def test_breached_thresholds_raise_alerts(self) -> None:
        monitor = ModelMonitor()
        alerts = monitor.check_health(
            {"drawdown": 0.30, "uncertainty": 0.9, "reward_decay": 0.5, "drift": 0.5}
        )
        self.assertIn("MAX_DRAWDOWN_WARNING", alerts)
        self.assertIn("MODEL_UNCERTAINTY_HIGH", alerts)
        self.assertIn("PERFORMANCE_DEGRADATION", alerts)
        self.assertIn("MODEL_DRIFT_DETECTED", alerts)
        # An alert-producing check is also recorded in the event log.
        self.assertTrue(monitor.events)

    def test_missing_metrics_default_to_zero(self) -> None:
        monitor = ModelMonitor()
        self.assertEqual(monitor.check_health({}), [])

    def test_custom_thresholds(self) -> None:
        thresholds = HealthThresholds()
        thresholds.MAX_DRAWDOWN = 0.05
        monitor = ModelMonitor(thresholds)
        self.assertIn("MAX_DRAWDOWN_WARNING", monitor.check_health({"drawdown": 0.06}))

    def test_log_returns_timestamped_record(self) -> None:
        monitor = ModelMonitor()
        record = monitor.log("startup")
        self.assertEqual(record["event"], "startup")
        self.assertIn("time", record)


@unittest.skipUnless(_HAS_TORCH, "torch not installed")
class LiveEngineTests(unittest.TestCase):
    def test_full_pipeline_wiring(self) -> None:
        import torch  # local import: only when torch is available

        from live_engine import AuroraLiveEngine

        latent_dim = 8

        class Encoder(torch.nn.Module):
            def forward(self, x):  # (batch, time, latent_dim)
                return torch.zeros(1, 4, latent_dim)

        class WorldModel(torch.nn.Module):
            def forward(self, latent):
                return {"uncertainty": torch.tensor(0.25), "z_future": latent[:, -1]}

        class Policy(torch.nn.Module):
            def forward(self, z):  # -> (action_mean, action_std)
                action = torch.tensor([1.0, 0.2, 0.02, 0.06])
                return action, torch.ones(4)

        class RegimeEngine:
            def evaluate(self, latent_np, features, uncertainty):
                return {"regime": _Regime.BULL_TREND}

        class RiskManager:
            def evaluate(self, action, portfolio, uncertainty, regime, confidence):
                return {"approved": True, "size": float(action[1].item())}

        engine = AuroraLiveEngine(
            encoder=Encoder(),
            world_model=WorldModel(),
            regime_engine=RegimeEngine(),
            policy=Policy(),
            risk_manager=RiskManager(),
        )

        analysis = engine.analyze_market(
            market_tensor=torch.zeros(1, 4, 3),
            regime_features={},
            portfolio={},
        )

        self.assertIn("raw_action", analysis)
        self.assertTrue(AuroraLiveEngine.approve_trade(analysis))

        signal = SignalGenerator().generate("NVDA", analysis)
        self.assertEqual(signal.regime, "BULL_TREND")
        self.assertTrue(signal.approved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
