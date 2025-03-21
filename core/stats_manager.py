"""
Statistics manager module.
Tracks and manages donation statistics.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class StatsManager:
    """Manages donation statistics."""

    def __init__(self, config_dir=None):
        """Initialize stats manager.

        Args:
            config_dir: Configuration directory path
        """
        if config_dir is None:
            config_dir = Path.home() / ".lolzteam-donate"

        self.config_dir = Path(config_dir)
        self.stats_file = self.config_dir / "stats.json"

        # Ensure the directory exists
        os.makedirs(self.config_dir, exist_ok=True)

        self.stats = self._load_stats()

    def _load_stats(self) -> Dict[str, Any]:
        """Load statistics from file.

        Returns:
            Statistics dictionary
        """
        default_stats = {
            "total_amount": 0.0,
            "donation_count": 0,
        }

        if not self.stats_file.exists():
            self._save_stats(default_stats)
            return default_stats

        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)

            # Ensure all keys exist
            for key, value in default_stats.items():
                if key not in stats:
                    stats[key] = value

            return stats
        except Exception as e:
            print(f"Error loading stats: {e}")
            return default_stats

    def _save_stats(self, stats=None) -> None:
        """Save statistics to file.

        Args:
            stats: Statistics to save (or use current stats)
        """
        if stats is None:
            stats = self.stats

        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=4)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def add_donation(self, amount: float) -> None:
        """Add a donation to the statistics.

        Args:
            amount: Donation amount
        """
        self.stats["total_amount"] += float(amount)
        self.stats["donation_count"] += 1
        self._save_stats()

    def get_total_amount(self) -> float:
        """Get total donation amount.

        Returns:
            Total amount
        """
        return self.stats.get("total_amount", 0.0)

    def get_donation_count(self) -> int:
        """Get total donation count.

        Returns:
            Donation count
        """
        return self.stats.get("donation_count", 0)

    def reset_stats(self) -> None:
        """Reset all statistics to zero."""
        self.stats["total_amount"] = 0.0
        self.stats["donation_count"] = 0
        self._save_stats()

    def format_total_amount(self) -> str:
        """Format the total amount as a string with currency.

        Returns:
            Formatted amount string
        """
        return f"{self.get_total_amount():.2f} RUB"
