"""
Authentication dialog for DonationAlerts and LOLZTEAM authorization.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QApplication, QFrame, QWidget
)

from config.settings import Settings
from core.auth_service import AuthenticationService
from core.donation_alerts import DonationAlertsAPI
from core.lolzteam import LolzteamAPI
from gui.title_bar import TitleBar


class AuthDialog(QDialog):
    """Dialog for authenticating with DonationAlerts or LOLZTEAM."""

    auth_success = pyqtSignal(str, str)  # service, token

    def __init__(
            self,
            service: str,
            auth_url: str,
            parent=None
    ):
        """Initialize authentication dialog.

        Args:
            service: Service name ("donation_alerts" or "lolzteam")
            auth_url: Authorization URL
            parent: Parent widget
        """
        super().__init__(parent, Qt.FramelessWindowHint)

        self.service = service
        self.auth_url = auth_url
        self.auth_service = AuthenticationService()
        self.settings = parent.settings if hasattr(parent, 'settings') else Settings()

        self.setWindowTitle(f"Авторизация в {service}")
        self.setMinimumSize(400, 250)

        # Make the dialog modal
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI elements."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create title bar
        self.title_bar = TitleBar(self, f"Авторизация в {self.service}")
        self.title_bar.close_clicked.connect(self.reject)
        # Remove minimize button functionality
        self.title_bar.minimize_button.setVisible(False)

        main_layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Create info label
        info_label = QLabel(
            f"Авторизация в {self.service} будет открыта "
            f"в вашем браузере по умолчанию. Пожалуйста, войдите и разрешите доступ приложению."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(info_label)

        # Create detail label
        detail_label = QLabel(
            "После авторизации вы будете перенаправлены на страницу, которая "
            "автоматически установит связь с этим приложением. Вы можете закрыть "
            "эту страницу после завершения авторизации."
        )
        detail_label.setWordWrap(True)
        detail_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(detail_label)

        # Separator
        line = QFrame()
        line.setObjectName("line")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(line)

        # Create status label
        self.status_label = QLabel("Готов к авторизации")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.status_label)

        # Button layout
        button_layout = QHBoxLayout()

        # Authenticate button
        self.auth_button = QPushButton("Начать авторизацию")
        self.auth_button.clicked.connect(self._start_authentication)

        # Cancel button
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.auth_button)
        button_layout.addWidget(self.cancel_button)

        content_layout.addLayout(button_layout)
        content_layout.addStretch()

        main_layout.addWidget(content_widget, 1)

        self.setLayout(main_layout)

    def _start_authentication(self):
        """Start the authentication process."""
        self.status_label.setText("Авторизация в процессе...")
        self.auth_button.setEnabled(False)

        # Открываем URL в браузере
        try:
            success = self.auth_service.authenticate_process(
                self.auth_url,
                on_success=self._on_auth_success,
                on_error=self._on_auth_error
            )

            if not success:
                self.status_label.setText("Не удалось начать авторизацию")
                self.auth_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
            self.auth_button.setEnabled(True)

    def _on_auth_success(self, token):
        """Handle successful authentication.

        Args:
            token: Authentication token
        """
        self.status_label.setText("Авторизация успешна")
        QApplication.processEvents()  # Обновляем интерфейс

        if self.service == "DonationAlerts":
            # Для DonationAlerts нужно обменять код на токен
            try:
                self.settings.update_donation_alerts_token(token)

                self.auth_success.emit("donation_alerts", token)
            except Exception as e:
                self.status_label.setText(f"Ошибка: {str(e)}")
                self.auth_button.setEnabled(True)
        else:
            try:
                self.settings.update_lolzteam_token(token)

                self.auth_success.emit("lolzteam", token)
            except Exception as e:
                self.status_label.setText(f"Ошибка: {str(e)}")
                self.auth_button.setEnabled(True)

    def _on_auth_error(self, error_message):
        """Handle authentication error.

        Args:
            error_message: Error message
        """
        self.status_label.setText(f"Ошибка: {error_message}")
        self.auth_button.setEnabled(True)


class DonationAlertsAuthDialog(AuthDialog):
    """Dialog for authenticating with DonationAlerts."""

    def __init__(self, donation_alerts_api: DonationAlertsAPI, parent=None):
        """Initialize DonationAlerts authentication dialog.

        Args:
            donation_alerts_api: DonationAlerts API client
            parent: Parent widget
        """
        # Get auth_url first - this is probably causing the crash
        try:
            auth_url = donation_alerts_api.login()
            print(f"Auth URL generated: {auth_url}")  # Print the start of the URL for debugging
        except Exception as e:
            print(f"Error generating auth URL: {str(e)}")
            # Provide a fallback URL to prevent crash
            auth_url = "about:blank"

        # Call parent constructor with the auth_url
        super().__init__("DonationAlerts", auth_url, parent)

        # Store the API for later use
        self.donation_alerts_api = donation_alerts_api
        self.settings = parent.settings if hasattr(parent, 'settings') else Settings()


class LolzteamAuthDialog(AuthDialog):
    """Dialog for authenticating with LOLZTEAM."""

    def __init__(self, lolzteam_api: LolzteamAPI, parent=None):
        """Initialize LOLZTEAM authentication dialog.

        Args:
            lolzteam_api: LOLZTEAM API client
            parent: Parent widget
        """
        auth_url = lolzteam_api.get_auth_url()

        super().__init__("LOLZTEAM", auth_url, parent)
        self.lolzteam_api = lolzteam_api
        self.settings = parent.settings if hasattr(parent, 'settings') else Settings()
