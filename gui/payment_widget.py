"""
Payment widget for displaying recent payments.
"""

import datetime
from typing import Dict, Any, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea
)


class PaymentItem(QFrame):
    """Widget for displaying a single payment."""

    def __init__(self, payment: Dict[str, Any], parent=None):
        """Initialize payment item.

        Args:
            payment: Payment data
            parent: Parent widget
        """
        super().__init__(parent)

        self.setObjectName("paymentItem")

        # Create layout
        layout = QVBoxLayout(self)

        # Username first
        username_label = QLabel(payment['username'])
        username_label.setObjectName("usernameLabel")
        layout.addWidget(username_label)

        # Header layout (amount and date)
        header_layout = QHBoxLayout()

        # Amount label
        amount_label = QLabel(f"{payment['amount']} RUB")
        amount_label.setObjectName("amountLabel")

        # Date label
        datetime_str = self._format_date(payment.get("datetime", 0))
        date_label = QLabel(datetime_str)
        date_label.setObjectName("dateLabel")
        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_layout.addWidget(amount_label)
        header_layout.addStretch()
        header_layout.addWidget(date_label)

        layout.addLayout(header_layout)

        # Comment label (if any)
        comment = payment.get("comment", "").strip()
        if comment:
            # Фильтруем комментарий через банворды если они есть
            from config.settings import Settings
            settings = Settings()
            banwords = settings.get("app", "banwords") or []

            if banwords:
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
            layout.addWidget(comment_label)

        self.setLayout(layout)

    def _format_date(self, timestamp: int) -> str:
        """Format timestamp as a readable date.

        Args:
            timestamp: Unix timestamp

        Returns:
            Formatted date string
        """
        if not timestamp:
            return "Unknown date"

        dt = datetime.datetime.fromtimestamp(timestamp)
        now = datetime.datetime.now()

        if dt.date() == now.date():
            return f"Today {dt.strftime('%H:%M')}"
        elif dt.date() == (now - datetime.timedelta(days=1)).date():
            return f"Yesterday {dt.strftime('%H:%M')}"
        else:
            return dt.strftime("%d.%m.%Y %H:%M")


class PaymentList(QScrollArea):
    """Widget for displaying a list of payments."""

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
        self.layout.insertWidget(0, item)
