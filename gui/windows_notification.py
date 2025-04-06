import logging
import os
import sys
from typing import Optional

from gui.resource_helper import resource_path

# Check if on Windows and import winotify if available
WINDOWS_NOTIFICATION_AVAILABLE = False
if sys.platform == 'win32':
    try:
        from winotify import Notification, audio

        WINDOWS_NOTIFICATION_AVAILABLE = True
    except ImportError:
        pass

logger = logging.getLogger("WindowsNotification")


class WindowsNotificationManager:
    """Windows notification manager for native toast notifications."""

    def __init__(self, app_name: str = "LOLZTEAM DONATE"):
        """Initialize Windows notification manager.

        Args:
            app_name: Application name
        """
        self.app_name = app_name
        self.available = WINDOWS_NOTIFICATION_AVAILABLE
        self.silent_mode = False
        self.logger = logging.getLogger("WindowsNotification")

        self.icon_path = resource_path("gui/resources/icons/app_icon.ico")

        if not os.path.exists(self.icon_path):
            self.logger.warning(f"Icon file not found: {self.icon_path}")
            self.icon_path = None

        if not self.available:
            self.logger.warning("Windows notifications not available: winotify package not installed")

    def set_silent_mode(self, silent: bool) -> None:
        """Set silent mode for notifications.

        Args:
            silent: Whether to enable silent mode
        """
        self.silent_mode = silent
        self.logger.info(f"Silent mode set to {silent}")

    def show_notification(
            self,
            title: str,
            message: str,
            duration: str = "short",
            notification_type: str = "info",
            silent: Optional[bool] = None
    ) -> None:
        """Show a Windows toast notification.

        Args:
            title: Notification title
            message: Notification message
            duration: Notification duration ("short" or "long")
            notification_type: Notification type ("info", "error", "success", "warning")
            silent: Whether to show notification silently (overrides silent_mode)
        """
        if not self.available:
            self.logger.info(f"Notification would show: {title} - {message}")
            return

        # Determine if silent based on parameter or class setting
        is_silent = self.silent_mode if silent is None else silent

        try:
            self.logger.info(f"Showing notification: {title} - {message}")
            toast = Notification(
                app_id=self.app_name,
                title=title,
                msg=message,
                icon=self.icon_path
            )

            # Set audio based on notification type and silent mode
            if is_silent:
                toast.set_audio(audio.Silent, loop=False)

            elif notification_type == "error":
                toast.set_audio(audio.LoopingAlarm, loop=False)
            elif notification_type == "success":
                toast.set_audio(audio.IM, loop=False)
            elif notification_type == "warning":
                toast.set_audio(audio.LoopingAlarm2, loop=False)
            else:
                toast.set_audio(audio.Default, loop=False)
            # Show the notification
            toast.show()

        except Exception as e:
            self.logger.error(f"Error showing Windows notification: {str(e)}")

    def show_error(self, message: str, title: str = "Ошибка") -> None:
        """Show an error notification.

        Args:
            message: Error message
            title: Error title
        """
        self.show_notification(title, message, notification_type="error")

    def show_success(self, message: str, title: str = "Успешно") -> None:
        """Show a success notification.

        Args:
            message: Success message
            title: Success title
        """
        self.show_notification(title, message, notification_type="success")

    def show_warning(self, message: str, title: str = "Предупреждение") -> None:
        """Show a warning notification.

        Args:
            message: Warning message
            title: Warning title
        """
        self.show_notification(title, message, notification_type="warning")

    def show_info(self, message: str, title: str = "Информация") -> None:
        """Show an info notification.

        Args:
            message: Info message
            title: Info title
        """
        self.show_notification(title, message, notification_type="info")
