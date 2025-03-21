"""
Main window for the LOLZTEAM DONATE application.
"""

import asyncio
import threading
from io import BytesIO

import requests
from PIL import Image
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QObject
from PyQt5.QtGui import QPixmap, QColor, QPalette
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QApplication, QSystemTrayIcon, QMenu, QAction,
    QGroupBox, QMessageBox
)

from config.settings import Settings
from core.donation_alerts import DonationAlertsAPI, Scopes
from core.lolzteam import LolzteamAPI
from core.payment_monitor import PaymentMonitor
from core.stats_manager import StatsManager
from gui.auth_dialog import DonationAlertsAuthDialog, LolzteamAuthDialog
from gui.notification import NotificationManager
from gui.payment_widget import PaymentList
from gui.resources.styles import get_main_style, get_notification_style, get_payment_style, ColorScheme
from gui.settings_dialog import SettingsDialog
from gui.title_bar import TitleBar


class AsyncHelper(QObject):
    """Helper class for running async functions in Qt."""

    # Signals
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    task_started = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.func = None
        self.args = None
        self.kwargs = None
        self._thread = None
        self._event_loop = None

    def run_async(self, func, *args, **kwargs):
        """Run an async function in a thread.

        Args:
            func: Async function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs

        # Create new thread to run the event loop if not already running
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run_async_thread, daemon=True)
            self._thread.start()
        else:
            # If thread is already running, just queue the new task
            self._queue_task()

    def _run_async_thread(self):
        """Run the event loop in a thread."""
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        try:
            # Queue the initial task
            self._queue_task()

            # Run event loop until it's stopped
            self._event_loop.run_forever()
        finally:
            self._event_loop.close()
            self._event_loop = None

    def _queue_task(self):
        """Queue a task in the event loop."""
        if self._event_loop is None:
            raise RuntimeError("Event loop is not running")

        # Create and queue the task
        asyncio.run_coroutine_threadsafe(self._run_task(), self._event_loop)

    async def _run_task(self):
        """Run the async function and emit signals."""
        try:
            # For start_monitoring, we'll treat it specially
            if self.func.__name__ == 'start' and hasattr(self.func.__self__, '_monitor_payments'):
                # Just call the function and emit task_started
                await self.func(*self.args, **self.kwargs)
                self.task_started.emit()
                # Don't emit finished for continuous tasks
            else:
                # For regular tasks, run normally and emit finished
                result = await self.func(*self.args, **self.kwargs)
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main window for the application."""

    def __init__(self):
        """Initialize main window."""
        super().__init__(None, Qt.FramelessWindowHint)  # Без стандартного заголовка окна

        self.settings = Settings()
        self.stats_manager = StatsManager()
        self.notification_manager = NotificationManager(self)
        self.async_helper = AsyncHelper(self)
        self.async_helper.finished.connect(self._on_async_finished)
        self.async_helper.error.connect(self._on_async_error)
        self.async_helper.task_started.connect(self._on_task_started)

        self.payment_update_queue = []
        self.payment_update_timer = QTimer(self)
        self.payment_update_timer.timeout.connect(self._process_payment_updates)
        self.payment_update_timer.start(100)  # Process updates every 100ms

        # Определяем текущую тему
        self.current_theme = self.settings.get("app", "theme") or "light"

        self.donation_alerts_api = None
        self.lolzteam_api = None
        self.payment_monitor = None
        self.monitoring_active = False

        self.waiting_for = None
        self.user_info = {
            "donation_alerts": None,
            "lolzteam": None
        }

        self._initialize_api_clients()

        self.setWindowTitle("LOLZTEAM DONATE")
        self._apply_theme()

        # Установка фиксированного размера окна
        self.setFixedSize(800, 800)

        # Disable cursor changes on the edges to prevent resize cursor
        self.setWindowFlag(Qt.MSWindowsFixedSizeDialogHint)  # Windows
        self.setFixedSize(self.size())  # Ensure it's truly fixed

        self._init_ui()
        self._init_tray_icon()

        # Загружаем профили пользователей
        self._load_user_profiles()

        # Start with system if configured
        if self.settings.get("app", "start_minimized"):
            self.hide()
        else:
            self.show()

    def _apply_theme(self):
        """Apply current theme to all widgets."""
        self.setStyleSheet(get_main_style(self.current_theme))
        self.notification_manager.set_stylesheet(get_notification_style(self.current_theme))

    def _initialize_api_clients(self):
        """Initialize API clients."""
        # DonationAlerts
        da_credentials = self.settings.get_donation_alerts_credentials()
        self.donation_alerts_api = DonationAlertsAPI(
            da_credentials["client_id"],
            da_credentials["redirect_uri"],
            [Scopes.USER_SHOW, Scopes.CUSTOM_ALERT_STORE]
        )

        # LOLZTEAM
        lzt_credentials = self.settings.get_lolzteam_credentials()
        self.lolzteam_api = LolzteamAPI(
            lzt_credentials["client_id"],
            lzt_credentials["redirect_uri"],
            lzt_credentials["access_token"]
        )

    def _init_ui(self):
        """Initialize UI elements."""
        # Создаем главный контейнер с вертикальной компоновкой
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Добавляем кастомный заголовок окна
        self.title_bar = TitleBar(self)
        self.title_bar.close_clicked.connect(self.close)
        self.title_bar.minimize_clicked.connect(self.showMinimized)

        main_layout.addWidget(self.title_bar)

        # Создаем основной виджет с контентом
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Create header
        header_layout = QHBoxLayout()

        # App title
        title_layout = QVBoxLayout()

        title_label = QLabel("LOLZTEAM DONATE")
        title_label.setObjectName("titleLabel")

        subtitle_label = QLabel("DonationAlerts Integration")
        subtitle_label.setObjectName("subtitleLabel")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Settings button
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self._show_settings)

        header_layout.addWidget(settings_button)

        content_layout.addLayout(header_layout)

        # Create horizontal line
        line = QFrame()
        line.setObjectName("line")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(line)

        # Create user profiles section
        profiles_layout = QHBoxLayout()

        # DonationAlerts profile
        self.donation_alerts_profile = QGroupBox("DonationAlerts")
        da_profile_layout = QVBoxLayout()

        self.da_profile_content = QWidget()
        self.da_profile_layout = QVBoxLayout(self.da_profile_content)
        self.da_profile_layout.setSpacing(2)  # Уменьшенный интервал между элементами

        self.da_auth_button = QPushButton("Authenticate with DonationAlerts")
        self.da_auth_button.clicked.connect(self._authenticate_donation_alerts)
        self.da_profile_layout.addWidget(self.da_auth_button)

        da_profile_layout.addWidget(self.da_profile_content)
        self.donation_alerts_profile.setLayout(da_profile_layout)

        # LOLZTEAM profile
        self.lolzteam_profile = QGroupBox("LOLZTEAM")
        lzt_profile_layout = QVBoxLayout()

        self.lzt_profile_content = QWidget()
        self.lzt_profile_layout = QVBoxLayout(self.lzt_profile_content)
        self.lzt_profile_layout.setSpacing(2)  # Уменьшенный интервал между элементами

        self.lzt_auth_button = QPushButton("Authenticate with LOLZTEAM")
        self.lzt_auth_button.clicked.connect(self._authenticate_lolzteam)
        self.lzt_profile_layout.addWidget(self.lzt_auth_button)

        lzt_profile_layout.addWidget(self.lzt_profile_content)
        self.lolzteam_profile.setLayout(lzt_profile_layout)

        profiles_layout.addWidget(self.donation_alerts_profile)
        profiles_layout.addWidget(self.lolzteam_profile)

        content_layout.addLayout(profiles_layout)

        # Статистика и управление
        control_layout = QHBoxLayout()

        # Статистика
        stats_group = QGroupBox("Donation Statistics")
        stats_layout = QVBoxLayout()
        stats_layout.setAlignment(Qt.AlignCenter)  # Центрируем содержимое

        # Общая сумма донатов (центрирована)
        self.total_amount_label = QLabel(self.stats_manager.format_total_amount())
        self.total_amount_label.setObjectName("totalAmountLabel")
        self.total_amount_label.setAlignment(Qt.AlignCenter)

        # Количество донатов
        self.donation_count_label = QLabel(f"Donation count: {self.stats_manager.get_donation_count()}")
        self.donation_count_label.setObjectName("statTitleLabel")
        self.donation_count_label.setAlignment(Qt.AlignCenter)

        stats_layout.addWidget(self.total_amount_label)
        stats_layout.addWidget(self.donation_count_label)

        stats_group.setLayout(stats_layout)

        # Управление мониторингом
        control_group = QGroupBox("Monitoring Control")
        control_buttons_layout = QVBoxLayout()

        # Fix button sizing by using a fixed width layout
        # Кнопка переключения мониторинга (одна кнопка вместо двух)
        self.toggle_monitoring_button = QPushButton("Start Monitoring")
        # self.toggle_monitoring_button.setObjectName("greenButton")
        self.toggle_monitoring_button.clicked.connect(self._toggle_monitoring)

        self.reload_payments_button = QPushButton("Reload Payments")
        self.reload_payments_button.clicked.connect(self._load_recent_payments)

        control_buttons_layout.addWidget(self.toggle_monitoring_button)
        control_buttons_layout.addWidget(self.reload_payments_button)

        control_group.setLayout(control_buttons_layout)

        control_layout.addWidget(stats_group)
        control_layout.addWidget(control_group)

        content_layout.addLayout(control_layout)

        # Create payments section
        payments_group = QGroupBox("Recent Payments")
        payments_layout = QVBoxLayout()

        self.payment_list = PaymentList()
        self.payment_list.setStyleSheet(get_payment_style(self.current_theme))

        # Set background roles explicitly
        self.payment_list.setAutoFillBackground(True)
        payments_group.setAutoFillBackground(True)

        # Ensure borders match the theme
        payments_layout.setContentsMargins(2, 2, 2, 2)

        payments_layout.addWidget(self.payment_list)
        payments_group.setLayout(payments_layout)
        content_layout.addWidget(payments_group)

        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Добавляем виджет с контентом в главный контейнер
        main_layout.addWidget(content_widget)

        # Устанавливаем главный контейнер как центральный виджет
        self.setCentralWidget(main_container)

        # Fix potential rendering artifacts at window corners
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)

        # Ensure consistent background color
        palette = self.palette()
        bg_color = ColorScheme.Dark.BACKGROUND_COLOR if hasattr(self,
                                                                'current_theme') else ColorScheme.Light.BACKGROUND_COLOR
        palette.setColor(QPalette.Window, QColor(bg_color))
        self.setPalette(palette)

    def _init_tray_icon(self):
        """Initialize system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("LOLZTEAM DONATE")

        # Create tray menu
        tray_menu = QMenu()

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)

        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(settings_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)

        # Use a default icon for now
        self.tray_icon.setIcon(self.style().standardIcon(QApplication.style().SP_ComputerIcon))
        self.tray_icon.show()

    def _toggle_monitoring(self):
        """Toggle payment monitoring on/off."""
        if self.monitoring_active:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        """Start monitoring for payments."""
        if not self.settings.is_donation_alerts_configured():
            self.notification_manager.show_error(
                "DonationAlerts is not configured. Please authenticate first.",
                "Configuration Error"
            )
            return

        if not self.settings.is_lolzteam_configured():
            self.notification_manager.show_error(
                "LOLZTEAM is not configured. Please authenticate first.",
                "Configuration Error"
            )
            return

        # Initialize payment monitor if not already done
        if not self.payment_monitor:
            self.payment_monitor = PaymentMonitor(
                self.lolzteam_api,
                self.donation_alerts_api,
                self.settings.get("app", "min_payment_amount"),
                self.settings.get("app", "check_interval_seconds")
            )

            # Set DonationAlerts token
            donation_alerts_token = self.settings.get("donation_alerts", "access_token")
            self.payment_monitor.set_donation_alerts_token(donation_alerts_token)

            # Set callbacks
            self.payment_monitor.set_on_payment_callback(self._on_new_payment)
            self.payment_monitor.set_on_error_callback(self._on_monitor_error)

            # Set new callback for payment list updates
            self.payment_monitor.set_on_payments_updated_callback(self._on_payments_updated)

        # Start the monitor
        self.waiting_for = "payment_monitor_start"
        self.status_bar.showMessage("Starting payment monitoring...")

        # Start monitoring in background - with improved AsyncHelper
        self.async_helper.run_async(self.payment_monitor.start)

        # Update UI will be done in _on_task_started when we receive the signal

    def _stop_monitoring(self):
        """Stop monitoring for payments."""
        if self.payment_monitor:
            self.waiting_for = "payment_monitor_stop"
            self.async_helper.run_async(self.payment_monitor.stop)

            # Update UI
            self.status_bar.showMessage("Stopping payment monitoring...")

            # Disable button temporarily to prevent multiple clicks
            self.toggle_monitoring_button.setEnabled(False)
            QTimer.singleShot(2000, lambda: self.toggle_monitoring_button.setEnabled(True))

    def _load_user_profiles(self):
        """Load user profiles if authenticated."""
        # Check DonationAlerts
        if self.settings.is_donation_alerts_configured():
            token = self.settings.get("donation_alerts", "access_token")
            self.waiting_for = "donation_alerts_profile"

            try:
                # Get user info
                user_info = self.donation_alerts_api.user(token)
                self._update_donation_alerts_profile(user_info)
            except Exception as e:
                self.notification_manager.show_error(
                    f"Failed to load DonationAlerts profile: {str(e)}"
                )

        # Check LOLZTEAM
        if self.settings.is_lolzteam_configured():
            self.waiting_for = "lolzteam_profile"

            try:
                # Get user info
                user_info = self.lolzteam_api.get_user_info()
                self._update_lolzteam_profile(user_info)
            except Exception as e:
                self.notification_manager.show_error(
                    f"Failed to load LOLZTEAM profile: {str(e)}"
                )

        # Load recent payments if LOLZTEAM is configured
        if self.settings.is_lolzteam_configured():
            self._load_recent_payments()

    def _load_recent_payments(self):
        """Load recent payments from LOLZTEAM."""
        try:
            print("Loading recent payments from LOLZTEAM...")
            # Убедимся, что у нас есть токен и API-клиент настроен
            if not self.lolzteam_api or not self.settings.is_lolzteam_configured():
                print("LOLZTEAM not configured, can't load payments")
                return

            min_amount = self.settings.get("app", "min_payment_amount")
            print(f"Getting payment history with min_amount={min_amount}")

            payments = self.lolzteam_api.get_payment_history(
                min_amount=min_amount,
            )

            print(f"Got {len(payments)} payments from API")

            self.payment_list.set_payments(payments)
            print("Payment list updated")

            # Обновляем статус
            self.status_bar.showMessage("Payments loaded successfully")
        except Exception as e:
            print(f"Error loading payments: {str(e)}")
            self.notification_manager.show_error(
                f"Не удалось загрузить историю платежей: {str(e)}"
            )

    def _on_payments_updated(self, new_payments):
        """Handle new payments update from monitor.

        Args:
            new_payments: List of new payments to add
        """
        if not new_payments:
            print("Warning: Received empty new payments list")
            return

        # Queue the updates to be processed in the main thread
        self.payment_update_queue.extend(new_payments)
        print(f"Queued {len(new_payments)} new payments for UI update, total queue: {len(self.payment_update_queue)}")

    def _process_payment_updates(self):
        """Process queued payment updates in the main thread."""
        if not self.payment_update_queue:
            return

        try:
            # Get the payments to process
            payments_to_process = self.payment_update_queue
            self.payment_update_queue = []

            print(f"Processing {len(payments_to_process)} payment updates")

            # Add each payment individually to avoid replacing the list
            for payment in payments_to_process:
                if "id" in payment and "amount" in payment and "username" in payment:
                    try:
                        self.payment_list.add_payment(payment)
                        print(
                            f"Added payment: ID={payment['id']}, Amount={payment['amount']}, User={payment['username']}")
                    except Exception as e:
                        print(f"Error adding payment to list: {str(e)}")
                else:
                    print(f"Skipping invalid payment: {payment}")

            # Update status
            self.status_bar.showMessage(f"Added {len(payments_to_process)} new payments")

        except Exception as e:
            print(f"Error processing payment updates: {str(e)}")

    def _update_donation_alerts_profile(self, user_info):
        """Update DonationAlerts profile widget.

        Args:
            user_info: User information from DonationAlerts
        """
        # Store user info
        self.user_info["donation_alerts"] = user_info

        # Clear current profile
        self._clear_layout(self.da_profile_layout)

        # Create profile layout
        profile_layout = QHBoxLayout()

        # Avatar
        avatar_url = user_info.get("data", {}).get("avatar", "")
        avatar_label = QLabel()
        avatar_label.setFixedSize(64, 64)

        if avatar_url:
            try:
                # Загружаем аватарку через requests
                response = requests.get(avatar_url)
                response.raise_for_status()
                data = response.content

                # Обрабатываем изображение
                img = Image.open(BytesIO(data))
                img = img.convert("RGBA")

                # Создаем круглую маску
                mask = Image.new("L", img.size, 0)
                from PIL import ImageDraw
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)

                # Применяем маску
                img.putalpha(mask)

                # Сохраняем в буфер и загружаем в QPixmap
                buf = BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                image_data = buf.read()

                # Загружаем QPixmap из байтовых данных
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)

                # Устанавливаем QPixmap в QLabel с масштабированием
                avatar_label.setPixmap(pixmap.scaled(
                    64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            except Exception as e:
                # Use placeholder
                avatar_label.setText("Avatar")
                print(f"Error loading avatar: {e}")
        else:
            # Use placeholder
            avatar_label.setText("Avatar")

        # User info
        user_layout = QVBoxLayout()
        user_layout.setSpacing(2)  # Уменьшенный интервал

        name = user_info.get("data", {}).get("name", "Unknown")
        name_label = QLabel(f"Name: {name}")
        name_label.setObjectName("usernameLabel")

        code = user_info.get("data", {}).get("code", "")
        code_label = QLabel(f"Code: {code}")

        user_layout.addWidget(name_label)
        user_layout.addWidget(code_label)

        # Reauth button
        reauth_button = QPushButton("Re-authenticate")
        reauth_button.setObjectName("secondaryButton")
        reauth_button.clicked.connect(self._authenticate_donation_alerts)

        profile_layout.addWidget(avatar_label)
        profile_layout.addLayout(user_layout, 1)
        profile_layout.addWidget(reauth_button)

        self.da_profile_layout.addLayout(profile_layout)
        self.da_profile_content.setVisible(True)

    def _update_lolzteam_profile(self, user_info):
        """Update LOLZTEAM profile widget.

        Args:
            user_info: User information from LOLZTEAM
        """
        # Store user info
        self.user_info["lolzteam"] = user_info

        # Clear current profile
        self._clear_layout(self.lzt_profile_layout)

        # Create profile layout
        profile_layout = QHBoxLayout()

        # Avatar
        avatar_url = user_info.get("user", {}).get("links", {}).get("avatar", "")
        avatar_label = QLabel()
        avatar_label.setFixedSize(64, 64)

        if avatar_url:
            try:
                # Загружаем аватарку через requests
                response = requests.get(avatar_url)
                response.raise_for_status()
                data = response.content

                # Обрабатываем изображение
                img = Image.open(BytesIO(data))
                img = img.convert("RGBA")

                # Создаем круглую маску
                mask = Image.new("L", img.size, 0)
                from PIL import ImageDraw
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)

                # Применяем маску
                img.putalpha(mask)

                # Сохраняем в буфер и загружаем в QPixmap
                buf = BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                image_data = buf.read()

                # Загружаем QPixmap из байтовых данных
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)

                # Устанавливаем QPixmap в QLabel с масштабированием
                avatar_label.setPixmap(pixmap.scaled(
                    64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            except Exception as e:
                # Use placeholder
                avatar_label.setText("Avatar")
                print(f"Error loading avatar: {e}")
        else:
            # Use placeholder
            avatar_label.setText("Avatar")

        # User info
        user_layout = QVBoxLayout()

        username = user_info.get("user", {}).get("username", "Unknown")
        username_label = QLabel(f"Username: {username}")
        username_label.setObjectName("usernameLabel")

        user_id = user_info.get("user", {}).get("user_id", "")
        user_id_label = QLabel(f"User ID: {user_id}")

        user_layout.addWidget(username_label)
        user_layout.addWidget(user_id_label)

        # Reauth button
        reauth_button = QPushButton("Re-authenticate")
        reauth_button.setObjectName("secondaryButton")
        reauth_button.clicked.connect(self._authenticate_lolzteam)

        profile_layout.addWidget(avatar_label)
        profile_layout.addLayout(user_layout, 1)
        profile_layout.addWidget(reauth_button)

        self.lzt_profile_layout.addLayout(profile_layout)
        self.lzt_profile_content.setVisible(True)

    def _clear_layout(self, layout):
        """Clear all widgets from a layout.

        Args:
            layout: Layout to clear
        """
        while layout.count():
            item = layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.settings, self.stats_manager, self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.theme_changed.connect(self._on_theme_changed)
        dialog.stats_reset.connect(self._on_stats_reset)
        dialog.factory_reset.connect(self._on_factory_reset)
        # Делаем модальным, чтобы блокировать родительское окно
        dialog.setModal(True)
        dialog.exec_()

    def _on_theme_changed(self, theme):
        """Handle theme change.

        Args:
            theme: New theme
        """
        if self.current_theme != theme:
            self.current_theme = theme
            self._apply_theme()
            self.payment_list.setStyleSheet(get_payment_style(theme))

    def _on_stats_reset(self):
        """Handle statistics reset."""
        self.total_amount_label.setText(self.stats_manager.format_total_amount())
        self.donation_count_label.setText(f"Donation count: {self.stats_manager.get_donation_count()}")

    def _on_factory_reset(self):
        """Handle factory reset."""
        # Перезагружаем приложение
        QMessageBox.information(
            self,
            "Factory Reset",
            "The application has been reset to factory defaults. "
            "Please restart the application."
        )
        self._quit()

    def _authenticate_donation_alerts(self):
        """Authenticate with DonationAlerts."""
        try:
            print("Creating DonationAlertsAuthDialog...")
            dialog = DonationAlertsAuthDialog(self.donation_alerts_api, self)
            print("Dialog created, connecting signal...")
            dialog.auth_success.connect(self._on_donation_alerts_auth_success)
            print("Signal connected, setting modal...")
            # Делаем модальным, чтобы блокировать родительское окно
            dialog.setModal(True)
            print("Executing dialog...")
            dialog.exec_()
            print("Dialog executed")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in _authenticate_donation_alerts: {str(e)}")
            print(f"Traceback: {error_details}")
            self.notification_manager.show_error(
                f"Error authenticating with DonationAlerts: {str(e)}",
                "Authentication Error"
            )

    def _authenticate_lolzteam(self):
        """Authenticate with LOLZTEAM."""
        try:
            print("Creating LolzteamAuthDialog...")
            dialog = LolzteamAuthDialog(self.lolzteam_api, self)
            print("Dialog created, connecting signal...")
            dialog.auth_success.connect(self._on_lolzteam_auth_success)
            print("Signal connected, setting modal...")
            # Делаем модальным, чтобы блокировать родительское окно
            dialog.setModal(True)
            print("Executing dialog...")
            dialog.exec_()
            print("Dialog executed")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in _authenticate_lolzteam: {str(e)}")
            print(f"Traceback: {error_details}")
            self.notification_manager.show_error(
                f"Error authenticating with Lolzteam: {str(e)}",
                "Authentication Error"
            )

    @pyqtSlot(str, str)
    def _on_donation_alerts_auth_success(self, service, token):
        """Handle successful DonationAlerts authentication.

        Args:
            service: Service name
            token: Access token
        """
        if service != "donation_alerts":
            return

        # Save token
        self.settings.update_donation_alerts_token(token)

        # Update profile
        try:
            user_info = self.donation_alerts_api.user(token)
            self._update_donation_alerts_profile(user_info)

            # self.notification_manager.show_success(
            #     f"Successfully authenticated with DonationAlerts as {user_info.get('data', {}).get('name', 'Unknown')}"
            # )
        except Exception as e:
            pass
            # self.notification_manager.show_error(
            #     f"Failed to get user info: {str(e)}"
            # )

    @pyqtSlot(str, str)
    def _on_lolzteam_auth_success(self, service, token):
        """Handle successful LOLZTEAM authentication.

        Args:
            service: Service name
            token: Access token
        """
        if service != "lolzteam":
            return

        print(f"LOLZTEAM authentication successful, token: {token[:10]}...")

        # Save token
        self.settings.update_lolzteam_token(token)

        # Update API client
        self.lolzteam_api.set_access_token(token)

        # Update profile
        try:
            print("Getting LOLZTEAM user info...")
            user_info = self.lolzteam_api.get_user_info()
            self._update_lolzteam_profile(user_info)

            username = user_info.get("user", {}).get("username", "Unknown")
            print(f"LOLZTEAM user: {username}")

            self.notification_manager.show_success(
                f"Успешная авторизация в LOLZTEAM под именем {username}"
            )

            # Load recent payments
            print("Loading recent payments...")
            self._load_recent_payments()
        except Exception as e:
            error_msg = f"Ошибка получения информации о пользователе: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.notification_manager.show_error(error_msg)

    def _on_settings_saved(self):
        """Handle settings saved event."""
        # Re-initialize API clients
        self._initialize_api_clients()

        # Reload user profiles
        self._load_user_profiles()

        # Обновляем монитор, если он активен
        if self.monitoring_active and self.payment_monitor:
            # Остановка и перезапуск монитора с новыми настройками
            self._stop_monitoring()
            # Монитор будет перезапущен автоматически после остановки

    def _on_new_payment(self, payment):
        """Handle new payment event.

        Args:
            payment: Payment data
        """
        print(f"New payment received: {payment}")

        # Add payment to list
        self.payment_list.add_payment(payment)

        # Add to statistics
        amount = payment.get("amount", 0)
        self.stats_manager.add_donation(amount)

        # Update total amount display
        self.total_amount_label.setText(self.stats_manager.format_total_amount())
        self.donation_count_label.setText(f"Donation count: {self.stats_manager.get_donation_count()}")

        # # Show notification
        # self.notification_manager.show_success(
        #     f"Новый платеж {payment['amount']} RUB от {payment['username']}",
        #     "Новый платеж"
        # )

    def _on_monitor_error(self, error_message):
        """Handle payment monitor error.

        Args:
            error_message: Error message
        """
        self.notification_manager.show_error(error_message, "Payment Monitor Error")

    @pyqtSlot(object)
    def _on_async_finished(self, result):
        """Handle async operation finished.

        Args:
            result: Result of the async operation
        """
        print(f"Async operation finished: {self.waiting_for}")

        if self.waiting_for == "payment_monitor_start":
            # This gets called when start() function returns, not when monitoring ends
            print("Payment monitor initialization complete")
            self.status_bar.showMessage("Мониторинг платежей запущен")
            self.waiting_for = None
        elif self.waiting_for == "payment_monitor_stop":
            print("Payment monitor stopped")
            self.status_bar.showMessage("Мониторинг платежей остановлен")

            # Update UI
            self.toggle_monitoring_button.setText("Start Monitoring")
            self.toggle_monitoring_button.setObjectName("greenButton")
            self.toggle_monitoring_button.setStyleSheet("/* */")  # Force style refresh
            self.toggle_monitoring_button.setEnabled(True)
            self.reload_payments_button.setEnabled(True)

            self.monitoring_active = False

            self.waiting_for = None

            # Если монитор был остановлен в процессе изменения настроек, перезапускаем его
            if hasattr(self, "_restart_after_stop") and self._restart_after_stop:
                self._restart_after_stop = False
                QTimer.singleShot(500, self._start_monitoring)  # Задержка для стабильности

    @pyqtSlot(str)
    def _on_async_error(self, error_message):
        """Handle async operation error.

        Args:
            error_message: Error message
        """
        self.notification_manager.show_error(error_message, "Async Operation Error")

        # Reset UI if needed
        if self.waiting_for == "payment_monitor_start":
            self.toggle_monitoring_button.setText("Start Monitoring")
            self.toggle_monitoring_button.setObjectName("greenButton")
            self.toggle_monitoring_button.setStyleSheet("/* */")  # Force style refresh
            self.toggle_monitoring_button.setEnabled(True)
            self.reload_payments_button.setEnabled(True)
            self.monitoring_active = False
        elif self.waiting_for == "payment_monitor_stop":
            self.toggle_monitoring_button.setText("Stop Monitoring")
            self.toggle_monitoring_button.setObjectName("dangerButton")
            self.toggle_monitoring_button.setStyleSheet("/* */")  # Force style refresh
            self.toggle_monitoring_button.setEnabled(True)
            self.reload_payments_button.setEnabled(False)
            self.monitoring_active = True

        self.waiting_for = None

    @pyqtSlot()
    def _on_task_started(self):
        """Handle long-running task started signal."""
        print("Received task_started signal")

        if self.waiting_for == "payment_monitor_start":
            print("Payment monitoring is now active in background")
            self.status_bar.showMessage("Мониторинг платежей запущен")

            # Update UI for active monitoring
            self.toggle_monitoring_button.setText("Stop Monitoring")
            self.toggle_monitoring_button.setObjectName("dangerButton")
            self.toggle_monitoring_button.setStyleSheet("/* */")  # Force style refresh
            self.reload_payments_button.setEnabled(False)

            self.monitoring_active = True
            self.waiting_for = None

    def _tray_activated(self, reason):
        """Handle tray icon activation.

        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def _quit(self):
        """Quit the application."""
        # Stop payment monitor
        if self.payment_monitor:
            asyncio.create_task(self.payment_monitor.stop())

        QApplication.quit()

    def closeEvent(self, event):
        """Handle window close event.

        Args:
            event: Close event
        """
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()

        # Show tray notification
        self.tray_icon.showMessage(
            "LOLZTEAM DONATE",
            "Application minimized to tray. Click the tray icon to restore.",
            QSystemTrayIcon.Information,
            2000
        )

    # 1. Инициализация менеджера уведомлений с обновленными настройками
    def initialize_notification_manager(self):
        """Инициализация менеджера уведомлений с настройками из конфигурации."""
        self.notification_manager = NotificationManager(self)

        # Загружаем стиль
        self.notification_manager.set_stylesheet(get_notification_style(self.current_theme))

        # Устанавливаем настройки звука
        sound_enabled = self.settings.get("app", "notification_sound_enabled")
        if sound_enabled is not None:
            self.notification_manager.set_sound_enabled(sound_enabled)

        # Устанавливаем таймаут уведомлений
        timeout = self.settings.get("app", "notification_timeout")
        if timeout is not None:
            self.notification_manager.set_auto_close_timeout(timeout)

        # Устанавливаем максимальное количество видимых уведомлений
        max_visible = self.settings.get("app", "max_visible_notifications")
        if max_visible is not None:
            self.notification_manager.max_visible_notifications = max_visible

    # 2. Обработка изменения настроек уведомлений
    def _on_settings_saved(self):
        """Обработка события сохранения настроек."""
        # Существующий код...

        # Обновляем настройки менеджера уведомлений
        sound_enabled = self.settings.get("app", "notification_sound_enabled")
        if sound_enabled is not None:
            self.notification_manager.set_sound_enabled(sound_enabled)

        timeout = self.settings.get("app", "notification_timeout")
        if timeout is not None:
            self.notification_manager.set_auto_close_timeout(timeout)

        max_visible = self.settings.get("app", "max_visible_notifications")
        if max_visible is not None:
            self.notification_manager.max_visible_notifications = max_visible

    # 3. Примеры использования разных типов уведомлений
    def show_notification_examples(self):
        """Показать примеры разных типов уведомлений."""
        # Информационное уведомление
        self.notification_manager.show_info(
            "Это информационное сообщение",
            "Информация"
        )

        # Уведомление об успехе
        self.notification_manager.show_success(
            "Операция успешно выполнена",
            "Успех"
        )

        # Предупреждающее уведомление
        self.notification_manager.show_warning(
            "Внимание! Эта операция может занять некоторое время",
            "Предупреждение"
        )

        # Уведомление об ошибке
        self.notification_manager.show_error(
            "Произошла ошибка при выполнении операции",
            "Ошибка"
        )
