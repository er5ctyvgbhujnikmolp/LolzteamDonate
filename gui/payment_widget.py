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
    """Widget for displaying a single payment."""

    # Signal to be sent when the repeat button is clicked
    repeat_clicked = pyqtSignal(dict)

    def __init__(self, payment: Dict[str, Any], parent=None):
        """Initialize payment item.

        Args:
            payment: Payment data
            parent: Parent widget
        """
        super().__init__(parent)

        # Save payment data for possible resending
        self.payment_data = payment.copy()
        self.logger = logging.getLogger("PaymentItem")

        self.setObjectName("paymentItem")

        # Create main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Top row with username, date, and refresh button
        top_row = QHBoxLayout()

        # Username (left)
        username_label = QLabel(payment.get('username', 'Unknown'))
        username_label.setObjectName("usernameLabel")
        username_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Payment date (center, right-aligned)
        datetime_str = self._format_date(payment.get("datetime", 0))
        date_label = QLabel(datetime_str)
        date_label.setObjectName("dateLabel")

        # Refresh button (right)
        refresh_button = QToolButton()
        refresh_button.setObjectName("refreshButton")
        refresh_button.setToolTip("Repeat")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.setText("⟳")
        refresh_button.clicked.connect(self._on_repeat_clicked)

        # Add elements to top row
        top_row.addWidget(username_label, 1)  # With stretch
        top_row.addWidget(date_label)
        top_row.addWidget(refresh_button)

        # Add top row to main layout
        layout.addLayout(top_row)

        # Payment amount
        amount_label = QLabel(f"{payment.get('amount', '0')} RUB")
        amount_label.setObjectName("amountLabel")
        amount_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(amount_label)

        # Comment (if any)
        if comment := payment.get("comment", "").strip():
            comment_label = QLabel(self._add_invisible_spaces(comment))
            comment_label.setObjectName("commentLabel")
            comment_label.setWordWrap(True)
            comment_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(comment_label)

        self.setLayout(layout)

    @staticmethod
    def _add_invisible_spaces(text, step=10):
        """Add invisible spaces to text to allow better word wrapping.

        Args:
            text: Text to process
            step: Number of characters between invisible spaces

        Returns:
            Processed text
        """
        return '\u200B'.join(text[i:i + step] for i in range(0, len(text), step))

    def _format_date(self, timestamp: int) -> str:
        """Format timestamp to readable date.

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

    def _on_repeat_clicked(self):
        """Handle repeat button click."""
        self.logger.info(f"Repeat button clicked for payment from {self.payment_data.get('username')}")
        # Send signal with payment data
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
