"""
AURORA-SWING

Experience Database
===================

A permanent trading memory. Every decision is stored with its full context —
market state, regime, confidence/uncertainty, reasoning variables and outcome —
not merely "BUY → PROFIT". This memory feeds prioritized replay and error
analysis in the continual-learning loop.
"""

from __future__ import annotations

import pickle
import sqlite3
from dataclasses import dataclass

__all__ = ["ExperienceRecord", "ExperienceDatabase"]


@dataclass
class ExperienceRecord:
    """One stored decision + outcome."""

    state: object
    action: object
    reward: float
    regime: int
    uncertainty: float
    timestamp: float


class ExperienceDatabase:
    """SQLite-backed store of :class:`ExperienceRecord` rows."""

    def __init__(self, path: str = "experiences.db") -> None:
        self.connection = sqlite3.connect(path)
        self._create_table()

    def _create_table(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY,
                state BLOB,
                action BLOB,
                reward REAL,
                regime INTEGER,
                uncertainty REAL,
                timestamp REAL
            )
            """
        )
        self.connection.commit()

    def store(self, experience: ExperienceRecord) -> None:
        self.connection.execute(
            "INSERT INTO experiences VALUES (NULL, ?, ?, ?, ?, ?, ?)",
            (
                pickle.dumps(experience.state),
                pickle.dumps(experience.action),
                experience.reward,
                experience.regime,
                experience.uncertainty,
                experience.timestamp,
            ),
        )
        self.connection.commit()

    def recent(self, limit: int = 10_000) -> list[tuple]:
        cursor = self.connection.execute(
            "SELECT * FROM experiences ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return cursor.fetchall()
