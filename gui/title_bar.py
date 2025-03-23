"""
Custom title bar widget for the application window.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


class TitleBar(QFrame):
    """Custom title bar with close and minimize buttons."""

    # Сигналы
    close_clicked = pyqtSignal()
    minimize_clicked = pyqtSignal()

    def __init__(self, parent=None, title="LOLZTEAM DONATE by llimonix", minimized=True):
        """Initialize title bar.

        Args:
            parent: Parent widget
            title: Window title
        """
        super().__init__(parent)
        self.setObjectName("titleBar")

        self.setFixedHeight(36)
        self.setMouseTracking(True)

        self._mouse_pressed = False
        self._mouse_position = None
        self._parent = parent
        self.minimized = minimized

        self._init_ui(title)

    def _init_ui(self, title):
        """Initialize UI elements.

        Args:
            title: Window title
        """
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setObjectName("windowTitle")

        # Buttons
        if self.minimized:
            self.minimize_button = QPushButton("—")
            self.minimize_button.setObjectName("windowButton")
            self.minimize_button.setToolTip("Minimize")
            self.minimize_button.clicked.connect(self.minimize_clicked.emit)

        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("closeButton")
        self.close_button.setToolTip("Close")
        self.close_button.clicked.connect(self.close_clicked.emit)

        # Add widgets to layout
        layout.addWidget(self.title_label)
        layout.addStretch()
        if self.minimized:
            layout.addWidget(self.minimize_button)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        """Handle mouse press event for window dragging.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._mouse_position = event.globalPos()
            self._initial_window_pos = self._parent.pos()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release event.

        Args:
            event: Mouse event
        """
        self._mouse_pressed = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move event for window dragging.

        Args:
            event: Mouse event
        """
        if event.buttons() == Qt.LeftButton and self._mouse_pressed:
            # Вычисляем смещение
            delta = event.globalPos() - self._mouse_position
            # Применяем смещение к позиции окна
            new_pos = self._initial_window_pos + delta
            self._parent.move(new_pos)

        super().mouseMoveEvent(event)
