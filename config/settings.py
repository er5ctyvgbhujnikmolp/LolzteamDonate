"""
Configuration management module for LOLZTEAM DONATE application.
Handles saving and loading of application settings and authentication tokens.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List


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
            "banwords": [],  # List of banned words for filtering
            "filter_urls": False,  # Whether to filter URLs from payment messages
            "silent_notifications": False  # Whether to show notifications silently
        }
    }

    def __init__(self):
        """Initialize settings manager."""
        self.logger = logging.getLogger("Settings")
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
                self.logger.info("Updated settings with new default values")

            return settings
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def _save_settings(self, settings: Dict[str, Any]) -> None:
        """Save settings to configuration file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            self.logger.info("Settings saved successfully")
        except IOError as e:
            self.logger.error(f"Error saving settings: {e}")

    def save(self) -> None:
        """Save current settings."""
        self._save_settings(self.settings)

    def get(self, section: str, key: str, default=None) -> Any:
        """Get a setting value.

        Args:
            section: Settings section
            key: Setting key
            default: Default value if setting doesn't exist

        Returns:
            Setting value
        """
        return self.settings.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a setting value.

        Args:
            section: Settings section
            key: Setting key
            value: Setting value
        """
        if section not in self.settings:
            self.settings[section] = {}

        self.settings[section][key] = value
        self.save()
        self.logger.info(f"Set {section}.{key} = {value}")

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
        self.logger.info("Settings reset to defaults")

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
            self.logger.info(f"Added banword: {word}")

    def remove_banword(self, word: str) -> None:
        """Remove a word from the banwords list.

        Args:
            word: Word to remove
        """
        current_banwords = self.get("app", "banwords") or []
        if word in current_banwords:
            current_banwords.remove(word)
            self.set("app", "banwords", current_banwords)
            self.logger.info(f"Removed banword: {word}")

    def get_banwords(self) -> List[str]:
        """Get the list of banwords.

        Returns:
            List of banwords
        """
        return self.get("app", "banwords") or []

    def clear_banwords(self) -> None:
        """Clear the banwords list."""
        self.set("app", "banwords", [])
        self.logger.info("Cleared all banwords")

    def is_url_filtering_enabled(self) -> bool:
        """Check if URL filtering is enabled.

        Returns:
            True if URL filtering is enabled
        """
        return self.get("app", "filter_urls", False)

    def set_url_filtering(self, enabled: bool) -> None:
        """Set URL filtering state.

        Args:
            enabled: Whether URL filtering should be enabled
        """
        self.set("app", "filter_urls", enabled)

    def is_silent_notifications_enabled(self) -> bool:
        """Check if silent notifications are enabled.

        Returns:
            True if silent notifications are enabled
        """
        return self.get("app", "silent_notifications", False)

    def set_silent_notifications(self, enabled: bool) -> None:
        """Set silent notifications state.

        Args:
            enabled: Whether notifications should be silent
        """
        self.set("app", "silent_notifications", enabled)

    def import_banwords_from_file(self, filepath: str) -> int:
        """Import banwords from a text file.

        Args:
            filepath: Path to text file with one word per line

        Returns:
            Number of words imported

        Raises:
            Exception: If file cannot be read
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]

            current_banwords = set(self.get("app", "banwords") or [])
            new_words = [word for word in words if word and word not in current_banwords]

            if new_words:
                updated_banwords = list(current_banwords) + new_words
                self.set("app", "banwords", updated_banwords)
                self.logger.info(f"Imported {len(new_words)} banwords from {filepath}")
            return len(new_words)
        except Exception as e:
            self.logger.error(f"Error importing banwords: {e}")
            raise

    def export_banwords_to_file(self, filepath: str) -> int:
        """Export banwords to a text file.

        Args:
            filepath: Path to text file to export to

        Returns:
            Number of words exported

        Raises:
            Exception: If file cannot be written
        """
        try:
            banwords = self.get_banwords()
            with open(filepath, 'w', encoding='utf-8') as f:
                for word in banwords:
                    f.write(f"{word}\n")
            self.logger.info(f"Exported {len(banwords)} banwords to {filepath}")
            return len(banwords)
        except Exception as e:
            self.logger.error(f"Error exporting banwords: {e}")
            raise

    def factory_reset(self) -> None:
        """Reset all settings to factory defaults and remove any user data."""
        # Remove all files in the configuration directory
        try:
            for file in self.config_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)

            # Restore default settings
            self.settings = self.DEFAULT_SETTINGS.copy()
            self.save()

            # Reset statistics
            from core.stats_manager import StatsManager
            stats_manager = StatsManager(self.config_dir)
            stats_manager.reset_stats()

            self.logger.info("Factory reset completed")
        except Exception as e:
            self.logger.error(f"Error during factory reset: {e}")
            raise
