import logging

from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QCheckBox, QStyleOptionButton, QStyle

from gui.resources.styles import ColorScheme

logger = logging.getLogger("CustomCheckbox")


class CustomCheckBox(QCheckBox):
    """Custom styled checkbox with the application's color scheme."""

    def __init__(self, text="", parent=None):
        """Initialize custom checkbox.
        
        Args:
            text: Checkbox text
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        # Initial theme setting - will be updated when theme changes
        self.current_theme = "light"

    def set_theme(self, theme):
        """Set the checkbox theme.
        
        Args:
            theme: Theme name ("light" or "dark")
        """
        self.current_theme = theme
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Override paint event to customize checkbox appearance.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        opt = QStyleOptionButton()
        self.initStyleOption(opt)

        # Get colors based on theme
        if self.current_theme == "dark":
            bg_color = QColor(ColorScheme.Dark.CARD_BACKGROUND)
            border_color = QColor(ColorScheme.Dark.BORDER_COLOR)
            text_color = QColor(ColorScheme.Dark.TEXT_COLOR)
        else:
            bg_color = QColor(ColorScheme.Light.CARD_BACKGROUND)
            border_color = QColor(ColorScheme.Light.BORDER_COLOR)
            text_color = QColor(ColorScheme.Light.TEXT_COLOR)
        check_color = QColor(ColorScheme.PRIMARY_COLOR)
        # Determine check state
        is_checked = self.isChecked()
        is_enabled = self.isEnabled()
        is_focused = self.hasFocus()
        is_hovered = opt.state & QStyle.State_MouseOver

        # Adjust colors for disabled state
        if not is_enabled:
            border_color.setAlpha(128)
            if is_checked:
                check_color.setAlpha(128)
            text_color.setAlpha(128)

        # Draw checkbox rect
        checkbox_rect = QRect(0, 0, self.height() - 4, self.height() - 4)
        checkbox_rect.moveCenter(QRect(0, 0, checkbox_rect.width(), self.height()).center())

        # Draw background
        painter.setPen(QPen(border_color, 1.5))
        painter.setBrush(QBrush(bg_color))

        # Change border color on hover/focus
        if is_hovered or is_focused:
            painter.setPen(QPen(check_color, 1.5))

        # Draw rounded rect
        painter.drawRoundedRect(checkbox_rect, 3, 3)

        # Draw checkmark if checked
        if is_checked:
            check_rect = checkbox_rect.adjusted(3, 3, -3, -3)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(check_color))
            painter.drawRoundedRect(check_rect, 2, 2)

        # Draw text
        text_rect = self.rect().adjusted(checkbox_rect.width() + 8, 0, 0, 0)
        painter.setPen(QPen(text_color))
        text_flags = Qt.AlignLeft | Qt.AlignVCenter
        painter.drawText(text_rect, text_flags, self.text())

    def sizeHint(self):
        """Override size hint to provide appropriate size.
        
        Returns:
            Suggested size
        """
        size = super().sizeHint()
        return QSize(size.width(), max(size.height(), 22))
