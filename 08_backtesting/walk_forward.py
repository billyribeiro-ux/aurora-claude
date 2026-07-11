"""
AURORA-SWING

Walk-Forward Validation Engine
==============================

Prevents overfitting. Instead of training once on all history and testing on a
held-out tail (which lets the model "see too much"), it repeatedly trains on a
rolling window and validates on the next, out-of-sample period — then moves
forward and repeats.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

__all__ = ["WalkForwardWindow", "WalkForwardEngine"]


@dataclass
class WalkForwardWindow:
    """One train/test split in the walk-forward schedule."""

    train_start: str
    train_end: str
    test_start: str
    test_end: str


class WalkForwardEngine:
    """Run a train → validate → advance loop over a list of windows."""

    def __init__(self, windows: list[WalkForwardWindow]) -> None:
        self.windows = windows

    def run(
        self,
        train_function: Callable[[str, str], Any],
        evaluate_function: Callable[[Any, str, str], Any],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for window in self.windows:
            model = train_function(window.train_start, window.train_end)
            result = evaluate_function(model, window.test_start, window.test_end)
            results.append({"window": window, "result": result})
        return results
