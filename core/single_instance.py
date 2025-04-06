import atexit
import logging
import socket

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QWidget

from gui.title_bar import TitleBar

logger = logging.getLogger("SingleInstance")


class SingleInstanceChecker:
    """Ensures only one instance of the application is running."""

    def __init__(self, app_name: str = "lolzteam_donate"):
        """Initialize single instance checker.

        Args:
            app_name: Application name
        """
        self.app_name = app_name
        self.lock_socket = None
        self.logger = logging.getLogger("SingleInstanceChecker")

    def try_acquire_lock(self) -> bool:
        """Try to acquire a lock for this application.

        Returns:
            True if lock was acquired, False if another instance is running
        """
        # Create a TCP socket
        self.lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Try to bind to a port based on the app name
            port = abs(hash(self.app_name)) % 10000 + 10000  # Generate a port in range 10000-20000
            self.lock_socket.bind(('localhost', port))
            # Register cleanup on exit
            atexit.register(self.release_lock)
            self.logger.info(f"Lock acquired on port {port}")
            return True
        except socket.error:
            # Port is already in use, which means another instance is running
            self.lock_socket = None
            self.logger.warning("Another instance is already running")
            return False

    def release_lock(self):
        """Release the lock."""
        if self.lock_socket:
            self.lock_socket.close()
            self.lock_socket = None
            self.logger.info("Lock released")


class AlreadyRunningDialog(QDialog):
    """Dialog shown when application is already running."""

    def __init__(self, parent=None):
        """Initialize dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent, Qt.FramelessWindowHint)
        self.setWindowTitle("Приложение уже запущено")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom title bar
        self.title_bar = TitleBar(self, "Приложение уже запущено", minimized=False)
        self.title_bar.close_clicked.connect(self.accept)
        layout.addWidget(self.title_bar)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)

        message_label = QLabel(
            "Другой экземпляр LOLZTEAM DONATE уже запущен. "
            "Пожалуйста, используйте существующий экземпляр."
        )
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)

        content_layout.addWidget(message_label)
        content_layout.addStretch()
        content_layout.addWidget(ok_button, 0, Qt.AlignCenter)

        # Add content to main layout
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget, 1)

        self.setLayout(layout)
