"""
Settings dialog for configuring the application.
"""

import asyncio
import threading

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QObject
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QCheckBox, QTabWidget, QWidget, QComboBox, QMessageBox, QListWidget
)

from core.donation_alerts import DonationAlertsAPI
from core.lolzteam import LolzteamAPI
from core.stats_manager import StatsManager
from gui.notification import NotificationManager
from gui.resources.styles import get_settings_style
from gui.title_bar import TitleBar


class AsyncHelper(QObject):
    """Helper class for running async functions in Qt."""

    finished = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.func = None
        self.args = None
        self.kwargs = None

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

        # Create new thread to run the event loop
        threading.Thread(target=self._run_async_thread, daemon=True).start()

    def _run_async_thread(self):
        """Run the async function in a thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(self.func(*self.args, **self.kwargs))
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(e)
        finally:
            loop.close()


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    settings_saved = pyqtSignal()
    theme_changed = pyqtSignal(str)
    stats_reset = pyqtSignal()
    factory_reset = pyqtSignal()

    def __init__(self, settings, stats_manager=None, parent=None):
        """Initialize settings dialog.

        Args:
            settings: Settings manager
            stats_manager: Statistics manager
            parent: Parent widget
        """
        super().__init__(parent, Qt.FramelessWindowHint)

        self.settings = settings
        self.stats_manager = stats_manager or StatsManager()
        self.notification_manager = NotificationManager(self)
        self.async_helper = AsyncHelper(self)
        self.async_helper.finished.connect(self._on_async_finished)

        self.original_values = {}

        self.setWindowTitle("Настройки")
        self.setMinimumWidth(500)
        self.setFixedWidth(600)  # Фиксированная ширина
        self.setFixedHeight(600)  # Фиксированная высота

        # Get current theme
        self.current_theme = settings.get("app", "theme") or "light"
        self.initial_theme = self.current_theme  # Запоминаем начальную тему
        self.setStyleSheet(get_settings_style(self.current_theme))

        self.waiting_for = None

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Initialize UI elements."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create title bar
        self.title_bar = TitleBar(self, "Настройки", minimized=False)
        self.title_bar.close_clicked.connect(self.reject)
        self.title_bar.minimize_clicked.connect(self.showMinimized)

        main_layout.addWidget(self.title_bar)

        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Create tab widget
        tab_widget = QTabWidget()

        # Create API tab
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        # DonationAlerts group
        donation_alerts_group = QGroupBox("DonationAlerts API")
        donation_alerts_layout = QFormLayout()

        self.donation_alerts_client_id = QLineEdit()
        self.donation_alerts_redirect_uri = QLineEdit()
        self.donation_alerts_redirect_uri.setReadOnly(True)
        self.donation_alerts_token = QLineEdit()
        self.donation_alerts_token.setObjectName("tokenField")
        self.donation_alerts_token.setEchoMode(QLineEdit.Password)

        donation_alerts_layout.addRow("Client ID:", self.donation_alerts_client_id)
        donation_alerts_layout.addRow("Redirect URI:", self.donation_alerts_redirect_uri)

        # Token layout with test button
        token_layout = QHBoxLayout()
        token_layout.addWidget(self.donation_alerts_token)

        self.test_donation_alerts_button = QPushButton("Проверить")
        self.test_donation_alerts_button.setObjectName("testButton")
        self.test_donation_alerts_button.clicked.connect(self._test_donation_alerts_token)

        token_layout.addWidget(self.test_donation_alerts_button)

        donation_alerts_layout.addRow("Access Token:", token_layout)

        self.donation_alerts_status = QLabel()
        donation_alerts_layout.addRow("Статус:", self.donation_alerts_status)

        donation_alerts_group.setLayout(donation_alerts_layout)

        # LOLZTEAM group
        lolzteam_group = QGroupBox("LOLZTEAM API")
        lolzteam_layout = QFormLayout()

        self.lolzteam_client_id = QLineEdit()
        self.lolzteam_redirect_uri = QLineEdit()
        self.lolzteam_redirect_uri.setReadOnly(True)
        self.lolzteam_token = QLineEdit()
        self.lolzteam_token.setObjectName("tokenField")
        self.lolzteam_token.setEchoMode(QLineEdit.Password)

        lolzteam_layout.addRow("Client ID:", self.lolzteam_client_id)
        lolzteam_layout.addRow("Redirect URI:", self.lolzteam_redirect_uri)

        # Token layout with test button
        token_layout = QHBoxLayout()
        token_layout.addWidget(self.lolzteam_token)

        self.test_lolzteam_button = QPushButton("Проверить")
        self.test_lolzteam_button.setObjectName("testButton")
        self.test_lolzteam_button.clicked.connect(self._test_lolzteam_token)

        token_layout.addWidget(self.test_lolzteam_button)

        lolzteam_layout.addRow("Access Token:", token_layout)

        self.lolzteam_status = QLabel()
        lolzteam_layout.addRow("Статус:", self.lolzteam_status)

        lolzteam_group.setLayout(lolzteam_layout)

        # Add groups to API tab
        api_layout.addWidget(donation_alerts_group)
        api_layout.addWidget(lolzteam_group)
        api_layout.addStretch()

        # Create Application tab
        app_tab = QWidget()
        app_layout = QVBoxLayout(app_tab)

        # Monitoring settings group
        monitoring_group = QGroupBox("Настройки мониторинга")
        monitoring_form = QFormLayout()

        # Минимальная сумма платежа (без стрелок)
        min_amount_layout = QHBoxLayout()
        self.min_payment_amount = QLineEdit()
        self.min_payment_amount.setValidator(QIntValidator(1, 10000, self.min_payment_amount))
        min_amount_layout.addWidget(self.min_payment_amount)
        min_amount_layout.addWidget(QLabel("RUB"))

        # Интервал проверки (без стрелок)
        check_interval_layout = QHBoxLayout()
        self.check_interval = QLineEdit()
        self.check_interval.setValidator(QIntValidator(1, 3600, self.check_interval))
        check_interval_layout.addWidget(self.check_interval)
        check_interval_layout.addWidget(QLabel("сек"))

        monitoring_form.addRow("Минимальная сумма:", min_amount_layout)
        monitoring_form.addRow("Интервал проверки:", check_interval_layout)

        monitoring_group.setLayout(monitoring_form)

        # Application settings group
        app_group = QGroupBox("Настройки приложения")
        app_form = QFormLayout()

        self.start_minimized = QCheckBox("Запускать свёрнутым")
        self.start_with_system = QCheckBox("Запускать вместе с системой")

        # Theme selector
        self.theme_selector = QComboBox()
        self.theme_selector.addItem("Светлая тема", "light")
        self.theme_selector.addItem("Тёмная тема", "dark")

        app_form.addRow(self.start_minimized)
        app_form.addRow(self.start_with_system)
        app_form.addRow("Тема:", self.theme_selector)

        app_group.setLayout(app_form)

        # Статистика и сброс
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()
        stats_layout.setAlignment(Qt.AlignCenter)

        # Данные статистики
        total_amount = self.stats_manager.format_total_amount()
        donation_count = self.stats_manager.get_donation_count()

        self.total_label = QLabel(f"Общая сумма: {total_amount}")
        self.total_label.setObjectName("statTitleLabel")
        self.total_label.setAlignment(Qt.AlignCenter)

        self.count_label = QLabel(f"Количество донатов: {donation_count}")
        self.count_label.setObjectName("statTitleLabel")
        self.count_label.setAlignment(Qt.AlignCenter)

        # Кнопка сброса на всю ширину
        reset_button = QPushButton("Сбросить статистику")
        reset_button.setObjectName("dangerButton")
        reset_button.clicked.connect(self._confirm_reset_stats)

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.count_label)
        stats_layout.addWidget(reset_button)

        stats_group.setLayout(stats_layout)

        # Add groups to Application tab
        app_layout.addWidget(monitoring_group)
        app_layout.addWidget(app_group)
        app_layout.addWidget(stats_group)

        # Factory reset кнопка
        factory_reset_button = QPushButton("Сброс к заводским настройкам")
        factory_reset_button.setObjectName("dangerButton")
        factory_reset_button.clicked.connect(self._confirm_factory_reset)
        app_layout.addWidget(factory_reset_button)

        app_layout.addStretch()

        # Add tabs to tab widget
        tab_widget.addTab(api_tab, "Настройки API")
        tab_widget.addTab(app_tab, "Настройки приложения")

        # Create Banwords tab
        banwords_tab = QWidget()
        banwords_layout = QVBoxLayout(banwords_tab)

        # Пояснение
        explanation_label = QLabel(
            "Список запрещенных слов, которые будут заменены звездочками в сообщениях донатов. "
            "Эти слова будут фильтроваться как в приложении, так и в сообщениях, отправляемых на DonationAlerts."
        )
        explanation_label.setWordWrap(True)
        banwords_layout.addWidget(explanation_label)

        # Список банвордов
        banwords_group = QGroupBox("Список запрещенных слов")
        banwords_group_layout = QVBoxLayout()

        self.banwords_list = QListWidget()

        # Кнопки управления банвордами
        banwords_buttons_layout = QHBoxLayout()

        self.add_banword_input = QLineEdit()
        self.add_banword_input.setPlaceholderText("Введите запрещенное слово")

        add_banword_button = QPushButton("Добавить")
        add_banword_button.clicked.connect(self._add_banword)

        remove_banword_button = QPushButton("Удалить")
        remove_banword_button.clicked.connect(self._remove_banword)
        remove_banword_button.setObjectName("dangerButton")

        banwords_buttons_layout.addWidget(self.add_banword_input)
        banwords_buttons_layout.addWidget(add_banword_button)
        banwords_buttons_layout.addWidget(remove_banword_button)

        banwords_group_layout.addWidget(self.banwords_list)
        banwords_group_layout.addLayout(banwords_buttons_layout)

        banwords_group.setLayout(banwords_group_layout)
        banwords_layout.addWidget(banwords_group)

        # Добавление вкладки
        tab_widget.addTab(banwords_tab, "Запрещенные слова")

        # Add tab widget to layout
        content_layout.addWidget(tab_widget)

        # Create buttons
        button_layout = QHBoxLayout()

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self._save_settings)

        cancel_button = QPushButton("Отмена")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        content_layout.addLayout(button_layout)

        # Add content widget to main layout
        main_layout.addWidget(content_widget, 1)

        self.setLayout(main_layout)

    def _load_settings(self):
        """Load settings from config."""
        # DonationAlerts
        self.donation_alerts_client_id.setText(
            self.settings.get("donation_alerts", "client_id")
        )
        self.donation_alerts_redirect_uri.setText(
            self.settings.get("donation_alerts", "redirect_uri")
        )

        token = self.settings.get("donation_alerts", "access_token") or ""
        self.donation_alerts_token.setText(token)

        if token:
            self._update_status_label(
                self.donation_alerts_status,
                "Действителен" if self.settings.is_donation_alerts_configured() else "Не проверено",
                self.settings.is_donation_alerts_configured()
            )
        else:
            self._update_status_label(
                self.donation_alerts_status,
                "Не настроено",
                None
            )

        # LOLZTEAM
        self.lolzteam_client_id.setText(
            self.settings.get("lolzteam", "client_id")
        )

        self.lolzteam_redirect_uri.setText(
            self.settings.get("lolzteam", "redirect_uri")
        )

        token = self.settings.get("lolzteam", "access_token") or ""
        self.lolzteam_token.setText(token)

        if token:
            self._update_status_label(
                self.lolzteam_status,
                "Действителен" if self.settings.is_lolzteam_configured() else "Не проверено",
                self.settings.is_lolzteam_configured()
            )
        else:
            self._update_status_label(
                self.lolzteam_status,
                "Не настроено",
                None
            )

        # Monitoring
        self.min_payment_amount.setText(
            str(self.settings.get("app", "min_payment_amount"))
        )
        self.check_interval.setText(
            str(self.settings.get("app", "check_interval_seconds"))
        )

        # App
        self.start_minimized.setChecked(
            self.settings.get("app", "start_minimized")
        )
        self.start_with_system.setChecked(
            self.settings.get("app", "start_with_system")
        )

        # Theme
        theme_index = self.theme_selector.findData(self.current_theme)
        if theme_index >= 0:
            self.theme_selector.setCurrentIndex(theme_index)

        # Banwords
        banwords = self.settings.get_banwords()
        for word in banwords:
            self.banwords_list.addItem(word)

        self._save_original_values()

    def _save_original_values(self):
        """Сохранить начальные значения настроек для отслеживания изменений."""
        # DonationAlerts
        self.original_values["donation_alerts_client_id"] = self.donation_alerts_client_id.text()
        self.original_values["donation_alerts_redirect_uri"] = self.donation_alerts_redirect_uri.text()
        self.original_values["donation_alerts_token"] = self.donation_alerts_token.text()

        # LOLZTEAM
        self.original_values["lolzteam_client_id"] = self.lolzteam_client_id.text()
        self.original_values["lolzteam_redirect_uri"] = self.lolzteam_redirect_uri.text()
        self.original_values["lolzteam_token"] = self.lolzteam_token.text()

        # Monitoring settings
        self.original_values["min_payment_amount"] = self.min_payment_amount.text()
        self.original_values["check_interval"] = self.check_interval.text()

        # App settings
        self.original_values["start_minimized"] = self.start_minimized.isChecked()
        self.original_values["start_with_system"] = self.start_with_system.isChecked()
        self.original_values["theme"] = self.theme_selector.currentData()

        banwords = [
            self.banwords_list.item(i).text()
            for i in range(self.banwords_list.count())
        ]
        self.original_values["banwords"] = banwords.copy()

    def _save_settings(self):
        """Save settings to config."""
        changes = self._get_changed_settings()

        # Сохраняем только изменённые настройки
        if "donation_alerts_client_id" in changes:
            self.settings.set(
                "donation_alerts",
                "client_id",
                self.donation_alerts_client_id.text()
            )

        if "donation_alerts_redirect_uri" in changes:
            self.settings.set(
                "donation_alerts",
                "redirect_uri",
                self.donation_alerts_redirect_uri.text()
            )

        if "donation_alerts_token" in changes:
            self.settings.set(
                "donation_alerts",
                "access_token",
                self.donation_alerts_token.text()
            )

        if "lolzteam_client_id" in changes:
            self.settings.set(
                "lolzteam",
                "client_id",
                self.lolzteam_client_id.text()
            )

        if "lolzteam_redirect_uri" in changes:
            self.settings.set(
                "lolzteam",
                "redirect_uri",
                self.lolzteam_redirect_uri.text()
            )

        if "lolzteam_token" in changes:
            self.settings.set(
                "lolzteam",
                "access_token",
                self.lolzteam_token.text()
            )

        # Monitoring settings
        if "min_payment_amount" in changes:
            try:
                min_amount = int(self.min_payment_amount.text())
                min_amount = max(min_amount, 1)
                self.settings.set("app", "min_payment_amount", min_amount)
            except (ValueError, TypeError):
                self.settings.set("app", "min_payment_amount", 1)

        if "check_interval" in changes:
            try:
                check_interval = int(self.check_interval.text())
                check_interval = max(check_interval, 1)
                self.settings.set("app", "check_interval_seconds", check_interval)
            except (ValueError, TypeError):
                self.settings.set("app", "check_interval_seconds", 30)

        # App settings
        if "start_minimized" in changes:
            self.settings.set(
                "app",
                "start_minimized",
                self.start_minimized.isChecked()
            )

        if "start_with_system" in changes:
            self.settings.set(
                "app",
                "start_with_system",
                self.start_with_system.isChecked()
            )

        # Theme - только при сохранении
        if "theme" in changes:
            selected_theme = self.theme_selector.currentData()
            self.settings.set("app", "theme", selected_theme)
            self.current_theme = selected_theme
            self.theme_changed.emit(selected_theme)

        # Banwords - сохраняем только если были изменения
        if "banwords" in changes:
            banwords = []
            for i in range(self.banwords_list.count()):
                item = self.banwords_list.item(i)
                banwords.append(item.text())

            self.settings.set("app", "banwords", banwords)

        # Сигнал о сохранении настроек отправляем только если были значимые изменения,
        # которые требуют обновления интерфейса
        if self._has_significant_changes(changes):
            self.settings_saved.emit()

        self.accept()

    def _get_changed_settings(self):
        """Получить список изменённых настроек."""
        changes = []

        # DonationAlerts
        if self.donation_alerts_client_id.text() != self.original_values["donation_alerts_client_id"]:
            changes.append("donation_alerts_client_id")

        if self.donation_alerts_redirect_uri.text() != self.original_values["donation_alerts_redirect_uri"]:
            changes.append("donation_alerts_redirect_uri")

        if self.donation_alerts_token.text() != self.original_values["donation_alerts_token"]:
            changes.append("donation_alerts_token")

        # LOLZTEAM
        if self.lolzteam_client_id.text() != self.original_values["lolzteam_client_id"]:
            changes.append("lolzteam_client_id")

        if self.lolzteam_redirect_uri.text() != self.original_values["lolzteam_redirect_uri"]:
            changes.append("lolzteam_redirect_uri")

        if self.lolzteam_token.text() != self.original_values["lolzteam_token"]:
            changes.append("lolzteam_token")

        # Monitoring settings
        if self.min_payment_amount.text() != self.original_values["min_payment_amount"]:
            changes.append("min_payment_amount")

        if self.check_interval.text() != self.original_values["check_interval"]:
            changes.append("check_interval")

        # App settings
        if self.start_minimized.isChecked() != self.original_values["start_minimized"]:
            changes.append("start_minimized")

        if self.start_with_system.isChecked() != self.original_values["start_with_system"]:
            changes.append("start_with_system")

        if self.theme_selector.currentData() != self.original_values["theme"]:
            changes.append("theme")

        current_banwords = [
            self.banwords_list.item(i).text()
            for i in range(self.banwords_list.count())
        ]
        if set(current_banwords) != set(self.original_values["banwords"]):
            changes.append("banwords")

        return changes

    @staticmethod
    def _has_significant_changes(changes):
        """Проверить, есть ли изменения, требующие обновления интерфейса."""
        # Эти изменения требуют обновления API-клиентов и интерфейса
        significant_changes = [
            "donation_alerts_client_id", "donation_alerts_redirect_uri", "donation_alerts_token",
            "lolzteam_client_id", "lolzteam_redirect_uri", "lolzteam_token",
            "min_payment_amount", "check_interval"
        ]

        return any(change in significant_changes for change in changes)

    def reject(self):
        """Handle dialog rejection."""
        super().reject()

    def _test_donation_alerts_token(self):
        """Test DonationAlerts token."""
        token = self.donation_alerts_token.text().strip()

        if not token:
            self._update_status_label(
                self.donation_alerts_status,
                "Токен не указан",
                False
            )
            return

        self._update_status_label(
            self.donation_alerts_status,
            "Проверка...",
            None
        )

        client_id = self.donation_alerts_client_id.text()
        redirect_uri = self.donation_alerts_redirect_uri.text()

        api = DonationAlertsAPI(client_id, redirect_uri)

        self.waiting_for = "donation_alerts"
        self.async_helper.run_async(api.verify_token, token)

    def _test_lolzteam_token(self):
        """Test LOLZTEAM token."""
        token = self.lolzteam_token.text().strip()

        if not token:
            self._update_status_label(
                self.lolzteam_status,
                "Токен не указан",
                False
            )
            return

        self._update_status_label(
            self.lolzteam_status,
            "Проверка...",
            None
        )

        api = LolzteamAPI()

        self.waiting_for = "lolzteam"
        self.async_helper.run_async(api.verify_token, token)

    def _add_banword(self):
        """Add banword to the list."""
        word = self.add_banword_input.text().strip()
        if not word:
            return

        existing_words = [
            self.banwords_list.item(i).text().lower()
            for i in range(self.banwords_list.count())
        ]
        if word.lower() in existing_words:
            return

        # Добавляем слово в список
        self.banwords_list.addItem(word)
        self.add_banword_input.clear()

        # Save immediately
        self._save_banwords()

    def _remove_banword(self):
        """Remove selected banword from the list."""
        selected_items = self.banwords_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            row = self.banwords_list.row(item)
            self.banwords_list.takeItem(row)

        # Save immediately
        self._save_banwords()

    def _save_banwords(self):
        """Save the current banwords list to settings."""
        banwords = []
        for i in range(self.banwords_list.count()):
            item = self.banwords_list.item(i)
            banwords.append(item.text())

        self.settings.set("app", "banwords", banwords)

    def _confirm_reset_stats(self):
        """Confirm statistics reset."""
        confirm = QMessageBox.question(
            self,
            "Сброс статистики",
            "Вы уверены, что хотите обнулить всю статистику?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self.stats_manager.reset_stats()

            # Update labels
            total_amount = self.stats_manager.format_total_amount()
            donation_count = self.stats_manager.get_donation_count()

            self.total_label.setText(f"Общая сумма: {total_amount}")
            self.count_label.setText(f"Количество донатов: {donation_count}")

            # Emit signal
            self.stats_reset.emit()

            # Show notification
            self.notification_manager.show_success("Statistics have been reset")

    def _confirm_factory_reset(self):
        """Confirm factory reset."""
        confirm = QMessageBox.question(
            self,
            "Сброс к заводским настройкам",
            "Вы уверены, что хотите сбросить приложение к заводским настройкам?\n\n"
            "При этом будут удалены все настройки, токены и статистика.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # Выполняем сброс
            self.settings.factory_reset()

            # Emit signal
            self.factory_reset.emit()

            # Show notification
            self.notification_manager.show_success("Application has been reset to factory defaults")

            # Закрываем диалог
            self.accept()

    @pyqtSlot(object)
    def _on_async_finished(self, result):
        """Handle async operation finished.

        Args:
            result: Result of the async operation
        """
        if self.waiting_for == "donation_alerts":
            if isinstance(result, Exception):
                self._update_status_label(
                    self.donation_alerts_status,
                    "Неверный токен",
                    False
                )
                self.notification_manager.show_error(
                    f"Failed to verify DonationAlerts token: {str(result)}"
                )
            else:
                is_valid = bool(result)
                self._update_status_label(
                    self.donation_alerts_status,
                    "Действительный" if is_valid else "Неверный токен",
                    is_valid
                )

            self.waiting_for = None
        elif self.waiting_for == "lolzteam":
            if isinstance(result, Exception):
                self._update_status_label(
                    self.lolzteam_status,
                    "Неверный токен",
                    False
                )
                self.notification_manager.show_error(
                    f"Failed to verify LOLZTEAM token: {str(result)}"
                )
            else:
                is_valid = bool(result)
                self._update_status_label(
                    self.lolzteam_status,
                    "Действительный" if is_valid else "Неверный токен",
                    is_valid
                )

            self.waiting_for = None

    @staticmethod
    def _update_status_label(label, text, is_valid):
        """Update status label.

        Args:
            label: Label to update
            text: Text to set
            is_valid: Whether the status is valid (True/False/None)
        """
        label.setText(text)

        if is_valid is True:
            label.setObjectName("validLabel")
        elif is_valid is False:
            label.setObjectName("invalidLabel")
        else:
            label.setObjectName("statusLabel")

        label.setStyleSheet("/* */")  # Force style refresh
