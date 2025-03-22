"""
Payment widget for displaying recent payments.
"""

import datetime
from typing import Dict, Any, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QToolButton
)


class PaymentItem(QFrame):
    """Виджет для отображения одного платежа."""

    # Сигнал, который будет отправляться при нажатии на кнопку повтора
    repeat_clicked = pyqtSignal(dict)

    def __init__(self, payment: Dict[str, Any], parent=None):
        """Инициализация элемента платежа.

        Args:
            payment: Данные платежа
            parent: Родительский виджет
        """
        super().__init__(parent)

        # Сохраняем данные платежа для возможности повторной отправки
        self.payment_data = payment.copy()

        self.setObjectName("paymentItem")

        # Создаем основной вертикальный layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Верхняя строка с никнеймом пользователя, датой и кнопкой рефреша
        top_row = QHBoxLayout()

        # Никнейм пользователя (слева)
        username_label = QLabel(payment['username'])
        username_label.setObjectName("usernameLabel")
        username_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Дата платежа (по центру, с выравниванием вправо)
        datetime_str = self._format_date(payment.get("datetime", 0))
        date_label = QLabel(datetime_str)
        date_label.setObjectName("dateLabel")

        # Кнопка рефреша (справа)
        refresh_button = QToolButton()
        refresh_button.setObjectName("refreshButton")
        refresh_button.setToolTip("Повторить")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.setText("⟳")
        refresh_button.clicked.connect(self._on_repeat_clicked)

        # Добавляем элементы в верхнюю строку
        top_row.addWidget(username_label, 1)  # С растяжением
        top_row.addWidget(date_label)
        top_row.addWidget(refresh_button)

        # Добавляем верхнюю строку в основной layout
        layout.addLayout(top_row)

        # Сумма платежа
        amount_label = QLabel(f"{payment['amount']} руб.")
        amount_label.setObjectName("amountLabel")
        amount_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(amount_label)

        if comment := payment.get("comment", "").strip():
            # Фильтруем комментарий через банворды если они есть
            from config.settings import Settings
            settings = Settings()
            if banwords := settings.get("app", "banwords") or []:
                # Заменяем каждое запрещенное слово на звездочки (case-insensitive)
                for word in banwords:
                    if word and len(word) > 0:  # Проверяем, что слово не пустое
                        # Используем регулярные выражения для поиска без учета регистра
                        import re
                        pattern = re.compile(re.escape(word), re.IGNORECASE)
                        comment = pattern.sub('*' * len(word), comment)

            comment_label = QLabel(f"\"{comment}\"")
            comment_label.setObjectName("commentLabel")
            comment_label.setWordWrap(True)
            comment_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(comment_label)

        self.setLayout(layout)

    def _format_date(self, timestamp: int) -> str:
        """Форматирование временной метки в читаемую дату.

        Args:
            timestamp: Unix timestamp

        Returns:
            Отформатированная строка даты
        """
        if not timestamp:
            return "Неизвестная дата"

        dt = datetime.datetime.fromtimestamp(timestamp)
        now = datetime.datetime.now()

        if dt.date() == now.date():
            return f"Сегодня {dt.strftime('%H:%M')}"
        elif dt.date() == (now - datetime.timedelta(days=1)).date():
            return f"Вчера {dt.strftime('%H:%M')}"
        else:
            return dt.strftime("%d.%m.%Y %H:%M")

    def _on_repeat_clicked(self):
        """Обработчик нажатия на кнопку повтора."""
        # Отправляем сигнал с данными платежа
        self.repeat_clicked.emit(self.payment_data)


class PaymentList(QScrollArea):
    """Widget for displaying a list of payments."""

    payment_repeat_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        """Initialize payment list.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumHeight(200)

        # Create container widget
        self.container = QWidget()
        self.container.setObjectName("paymentListContainer")

        # Create layout
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Add stretch to push items to the top
        self.layout.addStretch()

        self.setWidget(self.container)

    def clear(self):
        """Clear all payments."""
        # Remove all widgets except the stretch
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def set_payments(self, payments: List[Dict[str, Any]]):
        """Set the list of payments.

        Args:
            payments: List of payment data
        """
        self.clear()

        if not payments:
            # Add "No payments" label
            label = QLabel("No payments found")
            label.setAlignment(Qt.AlignCenter)
            self.layout.insertWidget(0, label)
            return

        # Add payment items in reverse order (newest first)
        for payment in payments:
            item = PaymentItem(payment)
            item.repeat_clicked.connect(self._on_payment_repeat)
            self.layout.insertWidget(0, item)

    def add_payment(self, payment: Dict[str, Any]):
        """Add a new payment to the list.

        Args:
            payment: Payment data
        """
        # Remove "No payments" label if it exists
        if self.layout.count() == 2:  # Stretch + potentially the "No payments" label
            item = self.layout.itemAt(0)
            if item.widget() and isinstance(item.widget(), QLabel):
                item.widget().deleteLater()

        # Add new payment item at the top
        item = PaymentItem(payment)
        item.repeat_clicked.connect(self._on_payment_repeat)
        self.layout.insertWidget(0, item)

    def _on_payment_repeat(self, payment: Dict[str, Any]):
        """Обработка сигнала повторения платежа.

        Args:
            payment: Данные платежа для повторной отправки
        """
        # Передаем сигнал дальше, в MainWindow
        self.payment_repeat_requested.emit(payment)
