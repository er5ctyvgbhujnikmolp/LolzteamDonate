"""
Исправленный класс уведомлений с устранением проблем прозрачности и позиционирования.
"""

import os

from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QApplication, QGraphicsOpacityEffect
)

from gui.resources.styles import get_notification_style, ColorScheme


class NotificationType:
    """Типы уведомлений."""
    ERROR = "notification_error"
    SUCCESS = "notification_success"
    WARNING = "notification_warning"
    INFO = "notification_info"

    @staticmethod
    def get_color(notification_type):
        """Получить цвет для типа уведомления."""
        if notification_type == NotificationType.ERROR:
            return ColorScheme.ERROR_COLOR
        elif notification_type == NotificationType.SUCCESS:
            return ColorScheme.SUCCESS_COLOR
        elif notification_type == NotificationType.WARNING:
            return ColorScheme.WARNING_COLOR
        else:  # INFO
            return ColorScheme.PRIMARY_COLOR


class Notification(QFrame):
    """Улучшенное уведомление с таймаутом и анимациями."""

    closed = pyqtSignal()

    def __init__(
            self,
            parent=None,
            title="Notification",
            message="",
            notification_type=NotificationType.INFO,
            timeout=5000,  # Время в миллисекундах до автоматического закрытия
            with_sound=True
    ):
        """Инициализация виджета уведомления.

        Args:
            parent: Родительский виджет
            title: Заголовок уведомления
            message: Сообщение уведомления
            notification_type: Тип уведомления
            timeout: Время до автоматического закрытия (0 - не закрывать)
            with_sound: Включить звуковое оповещение
        """
        super().__init__(parent)

        self.notification_type = notification_type
        self.timeout = timeout
        self.setObjectName("notification")
        self.setObjectName(notification_type)

        # Переопределяем цвет фона уведомления вручную (для надежности)
        self.bg_color = NotificationType.get_color(notification_type)

        # Применяем стиль с непрозрачным фоном
        self.setStyleSheet(f"""
            background-color: {self.bg_color}; 
            color: white; 
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.3);
        """)

        # Увеличенные размеры для лучшей видимости
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)

        # Установка флагов и атрибутов окна
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # Отключаем прозрачность для фона
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Не активировать окно при показе

        # Эффект прозрачности для анимации
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)  # Начинаем с полной непрозрачности
        self.setGraphicsEffect(self.opacity_effect)

        # Анимация мигания вместо исчезновения
        self.blink_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.blink_animation.setDuration(1000)  # 1 секунда на цикл мигания
        self.blink_animation.setLoopCount(4)  # 4 цикла мигания
        self.blink_animation.setKeyValueAt(0.0, 1.0)  # Начало - полная непрозрачность
        self.blink_animation.setKeyValueAt(0.5, 0.3)  # Середина - полупрозрачность
        self.blink_animation.setKeyValueAt(1.0, 1.0)  # Конец - полная непрозрачность
        self.blink_animation.finished.connect(self._on_blink_finished)

        # Таймер автозакрытия
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.start_closing)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)  # Увеличенные отступы

        # Create title bar
        title_bar = QHBoxLayout()

        title_label = QLabel(title)
        title_label.setObjectName("notificationTitle")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))  # Увеличенный шрифт
        title_label.setStyleSheet("color: white;")

        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.start_closing)
        close_button.setStyleSheet(
            "background-color: transparent; color: white; font-weight: bold; border: none;"
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }"
        )

        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(close_button)

        # Create message label
        message_label = QLabel(message)
        message_label.setObjectName("notificationMessage")
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 11))  # Увеличенный шрифт
        message_label.setStyleSheet("color: white;")

        # Add to layout
        layout.addLayout(title_bar)
        layout.addWidget(message_label)

        self.setLayout(layout)

        # Воспроизвести звук при создании, если включено
        if with_sound:
            self.play_sound()

    def play_sound(self):
        """Воспроизвести звуковое оповещение в зависимости от типа уведомления."""
        sound_file = None

        # В реальном приложении здесь нужно добавить пути к звуковым файлам
        # для разных типов уведомлений
        if self.notification_type == NotificationType.ERROR:
            sound_file = "sounds/error.wav"
        elif self.notification_type == NotificationType.SUCCESS:
            sound_file = "sounds/success.wav"
        elif self.notification_type == NotificationType.WARNING:
            sound_file = "sounds/warning.wav"
        else:  # INFO
            sound_file = "sounds/info.wav"

        # Проверяем, существует ли звуковой файл
        if sound_file and os.path.exists(sound_file):
            try:
                QSound.play(sound_file)
            except Exception as e:
                print(f"Ошибка воспроизведения звука: {e}")

    def show(self):
        """Показать уведомление с анимацией."""
        # Сначала расчитываем размер на основе контента
        self.adjustSize()

        # Position in the bottom right corner
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry(self.parentWidget() if self.parentWidget() else None)

        # Убедимся, что размеры корректные
        width = max(self.width(), 400)
        height = self.sizeHint().height()

        self.setFixedWidth(width)
        self.setFixedHeight(height)

        # Позиционируем уведомление
        self.move(
            screen_rect.width() - width - 30,
            screen_rect.height() - height - 30
        )

        # Активируем и отображаем
        self.raise_()
        super().show()

        # Запускаем таймер автозакрытия, если указан timeout
        if self.timeout > 0:
            self.close_timer.start(self.timeout)

    def start_closing(self):
        """Начать анимацию закрытия (мигания)."""
        # Остановить таймер, если он активен
        if self.close_timer.isActive():
            self.close_timer.stop()

        # Запустить анимацию мигания
        self.blink_animation.start()

    def _on_blink_finished(self):
        """Обработчик завершения анимации мигания."""
        # Закрываем уведомление после завершения анимации
        super().close()

    def enterEvent(self, event):
        """Обработка события наведения мыши - останавливаем таймер."""
        if self.close_timer.isActive():
            self.close_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Обработка события ухода мыши - перезапускаем таймер."""
        if self.timeout > 0:
            self.close_timer.start(self.timeout)
        super().leaveEvent(event)

    def closeEvent(self, event):
        """Обработка события закрытия."""
        # Если анимация мигания не активна, запускаем ее
        if not self.blink_animation.state() == QPropertyAnimation.Running:
            event.ignore()  # Игнорируем событие закрытия, чтобы показать анимацию
            self.start_closing()
        else:
            # Если анимация уже идет, эмитируем сигнал и принимаем событие
            self.closed.emit()
            event.accept()


class NotificationManager:
    """Управляет уведомлениями с поддержкой очереди."""

    def __init__(self, parent=None):
        """Инициализация менеджера уведомлений.

        Args:
            parent: Родительский виджет
        """
        self.parent = parent
        self.active_notifications = []
        self.notification_queue = []
        self.max_visible_notifications = 3  # Максимальное количество одновременно видимых уведомлений
        self.stylesheet = get_notification_style()

        # Загружаем настройки, если они доступны
        self.sound_enabled = True
        self.auto_close_timeout = 5000  # 5 секунд по умолчанию

        try:
            # Попытка загрузить настройки из конфигурации, если это возможно
            from config.settings import Settings
            settings = Settings()
            self.sound_enabled = settings.get("app", "notification_sound_enabled") if settings.get("app",
                                                                                                   "notification_sound_enabled") is not None else True
            self.auto_close_timeout = settings.get("app", "notification_timeout") if settings.get("app",
                                                                                                  "notification_timeout") is not None else 5000
        except (ImportError, AttributeError):
            # Используем значения по умолчанию, если не удалось загрузить
            pass

        # Создаем директорию для звуков, если ее нет
        os.makedirs("sounds", exist_ok=True)

    def set_stylesheet(self, stylesheet):
        """Установить таблицу стилей для уведомлений.

        Args:
            stylesheet: Строка таблицы стилей
        """
        self.stylesheet = stylesheet

    def set_sound_enabled(self, enabled):
        """Включить или выключить звуковые оповещения.

        Args:
            enabled: True для включения, False для выключения
        """
        self.sound_enabled = enabled

    def set_auto_close_timeout(self, timeout):
        """Установить время автозакрытия уведомлений.

        Args:
            timeout: Время в миллисекундах (0 - не закрывать автоматически)
        """
        self.auto_close_timeout = timeout

    def show_notification(
            self,
            title,
            message,
            notification_type=NotificationType.INFO
    ):
        """Показать уведомление.

        Args:
            title: Заголовок уведомления
            message: Сообщение уведомления
            notification_type: Тип уведомления
        """
        # Создаем новое уведомление
        notification = Notification(
            self.parent,
            title,
            message,
            notification_type,
            self.auto_close_timeout,
            self.sound_enabled
        )

        # Применяем текущую таблицу стилей (добавлено в само уведомление)
        # notification.setStyleSheet(self.stylesheet)

        notification.closed.connect(
            lambda: self._notification_closed(notification)
        )

        # Проверяем, можем ли мы показать больше уведомлений
        if len(self.active_notifications) >= self.max_visible_notifications:
            # Добавляем в очередь, если превышено максимальное количество
            self.notification_queue.append(notification)
        else:
            # Иначе показываем сразу
            self.active_notifications.append(notification)
            notification.show()
            # Не обновляем позиции, все уведомления размещаются в одном месте
            # self._update_positions()

    def show_error(self, message, title="Ошибка"):
        """Показать уведомление об ошибке.

        Args:
            message: Сообщение об ошибке
            title: Заголовок ошибки
        """
        self.show_notification(title, message, NotificationType.ERROR)

    def show_success(self, message, title="Успех"):
        """Показать уведомление об успехе.

        Args:
            message: Сообщение об успехе
            title: Заголовок успеха
        """
        self.show_notification(title, message, NotificationType.SUCCESS)

    def show_warning(self, message, title="Предупреждение"):
        """Показать предупреждающее уведомление.

        Args:
            message: Предупреждающее сообщение
            title: Заголовок предупреждения
        """
        self.show_notification(title, message, NotificationType.WARNING)

    def show_info(self, message, title="Информация"):
        """Показать информационное уведомление.

        Args:
            message: Информационное сообщение
            title: Заголовок информации
        """
        self.show_notification(title, message, NotificationType.INFO)

    def _notification_closed(self, notification):
        """Обработка события закрытия уведомления.

        Args:
            notification: Закрытое уведомление
        """
        if notification in self.active_notifications:
            self.active_notifications.remove(notification)

            # Показываем следующее уведомление из очереди, если есть
            self._process_queue()

    def _process_queue(self):
        """Обработка очереди уведомлений."""
        # Показываем уведомления из очереди, пока не достигнем максимального количества
        while self.notification_queue and len(self.active_notifications) < self.max_visible_notifications:
            next_notification = self.notification_queue.pop(0)
            self.active_notifications.append(next_notification)
            next_notification.show()
