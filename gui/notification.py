"""
Custom notification widget for displaying errors and messages.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QApplication
)

from gui.resources.styles import get_notification_style


class NotificationType:
    """Notification types."""
    ERROR = "notification_error"
    SUCCESS = "notification_success"
    WARNING = "notification_warning"
    INFO = "notification_info"


class Notification(QFrame):
    """Custom notification widget that requires manual closing."""

    closed = pyqtSignal()

    def __init__(
            self,
            parent=None,
            title="Notification",
            message="",
            notification_type=NotificationType.INFO
    ):
        """Initialize notification widget.

        Args:
            parent: Parent widget
            title: Notification title
            message: Notification message
            notification_type: Notification type
        """
        super().__init__(parent)

        self.setObjectName("notification")
        self.setObjectName(notification_type)

        # Увеличенные размеры для лучшей видимости
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)  # Увеличенные отступы

        # Create title bar
        title_bar = QHBoxLayout()

        title_label = QLabel(title)
        title_label.setObjectName("notificationTitle")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))  # Увеличенный шрифт

        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.close)

        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(close_button)

        # Create message label
        message_label = QLabel(message)
        message_label.setObjectName("notificationMessage")
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 11))  # Увеличенный шрифт

        # Add to layout
        layout.addLayout(title_bar)
        layout.addWidget(message_label)

        self.setLayout(layout)

    def show(self):
        """Show the notification."""
        # Position in the bottom right corner
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry(self)

        self.move(
            screen_rect.width() - self.width() - 30,  # Увеличен отступ от края
            screen_rect.height() - self.height() - 30  # Увеличен отступ от края
        )

        super().show()

    def closeEvent(self, event):
        """Handle close event."""
        self.closed.emit()
        super().closeEvent(event)


class NotificationManager:
    """Manages notifications."""

    def __init__(self, parent=None):
        """Initialize notification manager.

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.active_notifications = []
        self.stylesheet = get_notification_style()

    def set_stylesheet(self, stylesheet):
        """Set stylesheet for notifications.

        Args:
            stylesheet: Stylesheet string
        """
        self.stylesheet = stylesheet

    def show_notification(
            self,
            title,
            message,
            notification_type=NotificationType.INFO
    ):
        """Show a notification.

        Args:
            title: Notification title
            message: Notification message
            notification_type: Notification type
        """
        return
        notification = Notification(
            self.parent,
            title,
            message,
            notification_type
        )

        # Apply the current stylesheet
        notification.setStyleSheet(self.stylesheet)

        notification.closed.connect(
            lambda: self._notification_closed(notification)
        )

        self.active_notifications.append(notification)
        notification.show()

        self._update_positions()

    def show_error(self, message, title="Error"):
        """Show an error notification.

        Args:
            message: Error message
            title: Error title
        """
        print(message)
        # self.show_notification(title, message, NotificationType.ERROR)

    def show_success(self, message, title="Success"):
        """Show a success notification.

        Args:
            message: Success message
            title: Success title
        """
        print(message)
        # self.show_notification(title, message, NotificationType.SUCCESS)

    def show_warning(self, message, title="Warning"):
        """Show a warning notification.

        Args:
            message: Warning message
            title: Warning title
        """
        print(message)
        # self.show_notification(title, message, NotificationType.WARNING)

    def show_info(self, message, title="Information"):
        """Show an info notification.

        Args:
            message: Info message
            title: Info title
        """
        print(message)
        # self.show_notification(title, message, NotificationType.INFO)

    def _notification_closed(self, notification):
        """Handle notification closed event.

        Args:
            notification: Closed notification
        """
        if notification in self.active_notifications:
            self.active_notifications.remove(notification)
            self._update_positions()

    def _update_positions(self):
        """Update positions of active notifications."""
        if not self.active_notifications:
            return

        # Get the desktop
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry(self.parent)

        vertical_offset = 30  # Увеличенный отступ от края

        for notification in reversed(self.active_notifications):
            notification_height = notification.height()

            notification.move(
                screen_rect.width() - notification.width() - 30,  # Увеличенный отступ от края
                screen_rect.height() - notification_height - vertical_offset
            )

            vertical_offset += notification_height + 15  # Увеличенный интервал между уведомлениями
