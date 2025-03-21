"""
Configuration management module for LOLZTEAM DONATE application.
Handles saving and loading of application settings and authentication tokens.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List


class Settings:
    """Manages application settings and authentication tokens."""

    DEFAULT_SETTINGS = {
        "donation_alerts": {
            "client_id": "14617",
            "redirect_uri": "http://127.0.0.1:5228/login",
            "access_token": None
        },
        "lolzteam": {
            "client_id": "t93p9fol5e",
            "redirect_uri": "http://127.0.0.1:5228/lzt_login",
            "access_token": None
        },
        "app": {
            "min_payment_amount": 1,
            "check_interval_seconds": 3,
            "start_minimized": False,
            "start_with_system": False,
            "theme": "dark",
            "banwords": []  # Список запрещенных слов для фильтрации
        }
    }

    def __init__(self):
        """Initialize settings manager."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "settings.json"
        self.settings = self._load_settings()

    def _get_config_dir(self) -> Path:
        """Get the configuration directory path."""
        home_dir = Path.home()
        config_dir = home_dir / ".lolzteam-donate"
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from configuration file."""
        if not self.config_file.exists():
            self._save_settings(self.DEFAULT_SETTINGS)
            return self.DEFAULT_SETTINGS.copy()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                settings = json.load(f)

            # Ensure all default keys exist
            updated = False
            for section, values in self.DEFAULT_SETTINGS.items():
                if section not in settings:
                    settings[section] = values
                    updated = True
                else:
                    for key, value in values.items():
                        if key not in settings[section]:
                            settings[section][key] = value
                            updated = True

            if updated:
                self._save_settings(settings)

            return settings
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def _save_settings(self, settings: Dict[str, Any]) -> None:
        """Save settings to configuration file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings: {e}")

    def save(self) -> None:
        """Save current settings."""
        self._save_settings(self.settings)

    def get(self, section: str, key: str) -> Any:
        """Get a setting value."""
        return self.settings.get(section, {}).get(key)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a setting value."""
        if section not in self.settings:
            self.settings[section] = {}

        self.settings[section][key] = value
        self.save()

    def is_donation_alerts_configured(self) -> bool:
        """Check if DonationAlerts is configured."""
        token = self.get("donation_alerts", "access_token")
        return token is not None and token != ""

    def is_lolzteam_configured(self) -> bool:
        """Check if LOLZTEAM is configured."""
        token = self.get("lolzteam", "access_token")
        return token is not None and token != ""

    def update_donation_alerts_token(self, token: str) -> None:
        """Update DonationAlerts access token."""
        self.set("donation_alerts", "access_token", token)

    def update_lolzteam_token(self, token: str) -> None:
        """Update LOLZTEAM access token."""
        self.set("lolzteam", "access_token", token)

    def get_donation_alerts_credentials(self) -> Dict[str, str]:
        """Get DonationAlerts credentials."""
        return {
            "client_id": self.get("donation_alerts", "client_id"),
            "redirect_uri": self.get("donation_alerts", "redirect_uri"),
            "access_token": self.get("donation_alerts", "access_token")
        }

    def get_lolzteam_credentials(self) -> Dict[str, str]:
        """Get LOLZTEAM credentials."""
        return {
            "client_id": self.get("lolzteam", "client_id"),
            "redirect_uri": self.get("lolzteam", "redirect_uri"),
            "access_token": self.get("lolzteam", "access_token")
        }

    def reset(self) -> None:
        """Reset settings to default."""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save()

    def add_banword(self, word: str) -> None:
        """Add a word to the banwords list.

        Args:
            word: Word to add
        """
        if not word or len(word.strip()) == 0:
            return

        current_banwords = self.get("app", "banwords") or []
        if word not in current_banwords:
            current_banwords.append(word)
            self.set("app", "banwords", current_banwords)

    def remove_banword(self, word: str) -> None:
        """Remove a word from the banwords list.

        Args:
            word: Word to remove
        """
        current_banwords = self.get("app", "banwords") or []
        if word in current_banwords:
            current_banwords.remove(word)
            self.set("app", "banwords", current_banwords)

    def get_banwords(self) -> List[str]:
        """Get the list of banwords.

        Returns:
            List of banwords
        """
        return self.get("app", "banwords") or []

    def clear_banwords(self) -> None:
        """Clear the banwords list."""
        self.set("app", "banwords", [])

    def factory_reset(self) -> None:
        """Reset all settings to factory defaults and remove any user data."""
        # Удаляем все файлы в директории конфигурации
        try:
            for file in self.config_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)

            # Восстанавливаем настройки по умолчанию
            self.settings = self.DEFAULT_SETTINGS.copy()
            self.save()

            # Сбрасываем статистику
            from core.stats_manager import StatsManager
            stats_manager = StatsManager(self.config_dir)
            stats_manager.reset_stats()
        except Exception as e:
            print(f"Error during factory reset: {e}")
