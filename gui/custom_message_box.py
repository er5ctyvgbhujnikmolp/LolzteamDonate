import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)

from gui.title_bar import TitleBar

logger = logging.getLogger("CustomMessageBox")


class CustomMessageBox(QDialog):
    """Custom message box with title bar."""

    def __init__(
            self,
            parent=None,
            title="Message",
            message="",
            buttons=None,
            icon_type="question"
    ):
        """Initialize custom message box.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Dialog message
            buttons: List of button texts, defaults to ["Yes", "No"]
            icon_type: Icon type ("question", "information", "warning", "error")
        """
        super().__init__(parent, Qt.FramelessWindowHint)

        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        self.setModal(True)

        self.logger = logging.getLogger("CustomMessageBox")

        self.buttons = buttons or ["Yes", "No"]
        self.result_value = None

        self._init_ui(title, message, icon_type)

    def _init_ui(self, title, message, icon_type):
        """Initialize UI elements.

        Args:
            title: Dialog title
            message: Dialog message
            icon_type: Icon type
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom title bar
        self.title_bar = TitleBar(self, title, minimized=False)
        self.title_bar.close_clicked.connect(self.reject)
        layout.addWidget(self.title_bar)

        # Content layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(message_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        for btn_text in self.buttons:
            button = QPushButton(btn_text)

            # Set default button
            if btn_text in ["Да", "OK"]:
                button.setDefault(True)
                button.setFocus()
            elif btn_text in ["Нет", "Отмена"]:
                button.setObjectName("secondaryButton")

            # Connect button to result
            button.clicked.connect(lambda checked, text=btn_text: self._on_button_clicked(text))

            button_layout.addWidget(button)

        content_layout.addStretch()
        content_layout.addLayout(button_layout)

        # Add content to main layout
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget, 1)

        self.setLayout(layout)

    def _on_button_clicked(self, button_text):
        """Handle button click.

        Args:
            button_text: Text of the clicked button
        """
        self.logger.info(f"Button clicked: {button_text}")
        self.result_value = button_text
        self.accept()

    def get_result(self):
        """Get the dialog result.

        Returns:
            Button text that was clicked, or None if dialog was rejected
        """
        return self.result_value

    @staticmethod
    def question(parent, title, message, buttons=None):
        """Show a question message box.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Dialog message
            buttons: List of button texts, defaults to ["Yes", "No"]

        Returns:
            Button text that was clicked, or None if dialog was rejected
        """
        buttons = buttons or ["Да", "Нет"]
        dialog = CustomMessageBox(parent, title, message, buttons, "question")
        dialog.exec_()
        return dialog.get_result()

    @staticmethod
    def information(parent, title, message, buttons=None):
        """Show an information message box.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Dialog message
            buttons: List of button texts, defaults to ["OK"]

        Returns:
            Button text that was clicked, or None if dialog was rejected
        """
        buttons = buttons or ["OK"]
        dialog = CustomMessageBox(parent, title, message, buttons, "information")
        dialog.exec_()
        return dialog.get_result()

    @staticmethod
    def warning(parent, title, message, buttons=None):
        """Show a warning message box.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Dialog message
            buttons: List of button texts, defaults to ["OK"]

        Returns:
            Button text that was clicked, or None if dialog was rejected
        """
        buttons = buttons or ["OK"]
        dialog = CustomMessageBox(parent, title, message, buttons, "warning")
        dialog.exec_()
        return dialog.get_result()

    @staticmethod
    def error(parent, title, message, buttons=None):
        """Show an error message box.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Dialog message
            buttons: List of button texts, defaults to ["OK"]

        Returns:
            Button text that was clicked, or None if dialog was rejected
        """
        buttons = buttons or ["OK"]
        dialog = CustomMessageBox(parent, title, message, buttons, "error")
        dialog.exec_()
        return dialog.get_result()
