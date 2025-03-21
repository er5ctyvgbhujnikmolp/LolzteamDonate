"""
Style definitions for the application GUI.
"""


# Цветовые схемы
class ColorScheme:
    """Color schemes for light and dark themes."""

    # Основные цвета фирменного стиля (одинаковы для обеих тем)
    PRIMARY_COLOR = "#2BAD72"
    SECONDARY_COLOR = "#27996A"
    ERROR_COLOR = "#884444"  # Изменен на запрошенный цвет
    SUCCESS_COLOR = "#27AE60"
    WARNING_COLOR = "#F39C12"

    # Светлая тема
    class Light:
        BACKGROUND_COLOR = "#F5F5F5"
        CARD_BACKGROUND = "#FFFFFF"
        TEXT_COLOR = "#333333"
        SECONDARY_TEXT_COLOR = "#666666"
        BORDER_COLOR = "#DDDDDD"
        HEADER_COLOR = "#EEEEEE"
        SCROLL_BACKGROUND = "#F0F0F0"
        SCROLL_HANDLE = "#CCCCCC"
        HOVER_COLOR = "#E8E8E8"
        BUTTON_TEXT_COLOR = "#000000"  # Добавлен цвет текста кнопок для светлой темы

    # Темная тема
    class Dark:
        BACKGROUND_COLOR = "#141414"
        CARD_BACKGROUND = "#1E1E1E"
        TEXT_COLOR = "#EEEEEE"
        SECONDARY_TEXT_COLOR = "#AAAAAA"
        BORDER_COLOR = "#333333"
        HEADER_COLOR = "#252525"
        SCROLL_BACKGROUND = "#252525"
        SCROLL_HANDLE = "#444444"
        HOVER_COLOR = "#2A2A2A"
        BUTTON_TEXT_COLOR = "#FFFFFF"  # Добавлен цвет текста кнопок для темной темы


def get_main_style(theme="light"):
    """Get main style for the application.

    Args:
        theme: "light" or "dark"

    Returns:
        Style sheet string
    """
    # Выбираем цветовую схему в зависимости от темы
    colors = ColorScheme.Light if theme == "light" else ColorScheme.Dark

    return f"""
    QWidget {{
        background-color: {colors.BACKGROUND_COLOR};
        color: {colors.TEXT_COLOR};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 10pt;
    }}

    QLabel {{
        color: {colors.TEXT_COLOR};
        background-color: transparent;
    }}

    QLabel#titleLabel {{
        font-size: 18pt;
        font-weight: bold;
        color: {ColorScheme.PRIMARY_COLOR};
    }}

    QLabel#subtitleLabel {{
        font-size: 10pt;
        color: {colors.SECONDARY_TEXT_COLOR};
    }}

    QPushButton {{
        background-color: {ColorScheme.PRIMARY_COLOR};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: {ColorScheme.SECONDARY_COLOR};
    }}

    QPushButton:pressed {{
        background-color: {ColorScheme.SECONDARY_COLOR};
    }}

    QPushButton:disabled {{
        background-color: #AAAAAA;
        color: #555555;
    }}

    QPushButton#secondaryButton {{
        background-color: transparent;
        color: {colors.TEXT_COLOR};
        border: 1px solid {colors.BORDER_COLOR};
    }}

    QPushButton#secondaryButton:hover {{
        background-color: {colors.HOVER_COLOR};
    }}

    QPushButton#dangerButton {{
        background-color: {ColorScheme.ERROR_COLOR};
    }}

    QPushButton#dangerButton:hover {{
        background-color: #773333;
    }}
    
    QPushButton#greenButton {{
        background-color: {ColorScheme.PRIMARY_COLOR};
    }}

    QPushButton#greenButton:hover {{
        background-color: {ColorScheme.SECONDARY_COLOR};;
    }}
    
    QPushButton#toggleButton {{
        background-color: transparent;
        color: {colors.TEXT_COLOR};
        border: 1px solid {colors.BORDER_COLOR};
        padding: 4px 8px;
    }}

    QPushButton#toggleButton:checked {{
        background-color: {ColorScheme.PRIMARY_COLOR};
        color: white;
        border: none;
    }}

    QLineEdit, QTextEdit, QComboBox {{
        background-color: {colors.CARD_BACKGROUND};
        color: {colors.TEXT_COLOR};
        border: 1px solid {colors.BORDER_COLOR};
        border-radius: 4px;
        padding: 6px;
    }}

    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 1px solid {ColorScheme.PRIMARY_COLOR};
    }}

    QGroupBox {{
        border: 1px solid {colors.BORDER_COLOR};
        border-radius: 4px;
        margin-top: 12px;
        font-weight: bold;
        background-color: {colors.CARD_BACKGROUND};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px;
        color: {colors.TEXT_COLOR};
        background-color: {colors.CARD_BACKGROUND};
    }}

    QStatusBar {{
        background-color: {colors.HEADER_COLOR};
        color: {colors.TEXT_COLOR};
    }}

    QProgressBar {{
        border: 1px solid {colors.BORDER_COLOR};
        border-radius: 4px;
        text-align: center;
        background-color: {colors.CARD_BACKGROUND};
    }}

    QProgressBar::chunk {{
        background-color: {ColorScheme.PRIMARY_COLOR};
    }}

    QTabWidget::pane {{
        border: 1px solid {colors.BORDER_COLOR};
        border-radius: 4px;
        background-color: {colors.CARD_BACKGROUND};
    }}

    QTabBar::tab {{
        background-color: {colors.HEADER_COLOR};
        color: {colors.TEXT_COLOR};
        border: 1px solid {colors.BORDER_COLOR};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 6px 12px;
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background-color: {ColorScheme.PRIMARY_COLOR};
        color: white;
    }}

    QTabBar::tab:!selected:hover {{
        background-color: {colors.HOVER_COLOR};
    }}

    QTableWidget {{
        border: 1px solid {colors.BORDER_COLOR};
        border-radius: 4px;
        gridline-color: {colors.BORDER_COLOR};
        selection-background-color: {ColorScheme.PRIMARY_COLOR};
        selection-color: white;
        background-color: {colors.CARD_BACKGROUND};
        color: {colors.TEXT_COLOR};
    }}

    QTableWidget::item {{
        padding: 4px;
    }}

    QHeaderView::section {{
        background-color: {colors.HEADER_COLOR};
        color: {colors.TEXT_COLOR};
        padding: 6px;
        border: none;
        border-right: 1px solid {colors.BORDER_COLOR};
        border-bottom: 1px solid {colors.BORDER_COLOR};
    }}

    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 6px;  /* Тоньше скролл */
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {colors.SCROLL_HANDLE};
        border-radius: 3px;
        min-height: 20px;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        border: none;
        background: transparent;
        height: 6px;  /* Тоньше скролл */
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {colors.SCROLL_HANDLE};
        border-radius: 3px;
        min-width: 20px;
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QFrame#line {{
        background-color: {colors.BORDER_COLOR};
    }}

    QFrame#card {{
        background-color: {colors.CARD_BACKGROUND};
        border-radius: 8px;
        border: 1px solid {colors.BORDER_COLOR};
    }}
    
    /* Стили для кастомного заголовка окна */
    QFrame#titleBar {{
        background-color: {colors.HEADER_COLOR};
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    
    QPushButton#windowButton {{
        background-color: transparent;
        color: {colors.TEXT_COLOR};
        border: none;
        padding: 4px;
        border-radius: 2px;
        min-width: 20px;
        min-height: 20px;
        max-width: 20px;
        max-height: 20px;
    }}
    
    QPushButton#closeButton {{
        background-color: transparent;
        color: {colors.TEXT_COLOR};
        border: none;
        padding: 4px;
        border-radius: 2px;
        min-width: 20px;
        min-height: 20px;
        max-width: 20px;
        max-height: 20px;
    }}
    
    QPushButton#closeButton:hover {{
        background-color: {ColorScheme.ERROR_COLOR};
        color: white;
    }}
    
    QPushButton#windowButton:hover {{
        background-color: {colors.HOVER_COLOR};
    }}
    
    QLabel#windowTitle {{
        font-weight: bold;
        color: {colors.TEXT_COLOR};
    }}
    
    /* Стили для информации о сумме */
    QLabel#totalAmountLabel {{
        font-size: 14pt;
        font-weight: bold;
        color: {ColorScheme.PRIMARY_COLOR};
        qproperty-alignment: AlignCenter;
    }}
    
    QLabel#amountTitleLabel {{
        font-size: 12pt;
        color: {colors.SECONDARY_TEXT_COLOR};
        qproperty-alignment: AlignCenter;
    }}
    
    QLabel#statValueLabel {{
        font-weight: bold;
        color: {colors.TEXT_COLOR};
        qproperty-alignment: AlignCenter;
    }}
    
    QLabel#statTitleLabel {{
        color: {colors.TEXT_COLOR};
        qproperty-alignment: AlignCenter;
    }}
    """


def get_notification_style(theme="light"):
    """Get notification style.

    Args:
        theme: "light" or "dark"

    Returns:
        Style sheet string
    """
    # Для уведомлений используем одинаковый стиль в обеих темах

    return f"""
    QFrame#notification {{
        border-radius: 6px;
        padding: 8px;
    }}

    QFrame#notification_error {{
        background-color: {ColorScheme.ERROR_COLOR};
        color: white;
    }}

    QFrame#notification_success {{
        background-color: {ColorScheme.SUCCESS_COLOR};
        color: white;
    }}

    QFrame#notification_warning {{
        background-color: {ColorScheme.WARNING_COLOR};
        color: white;
    }}

    QFrame#notification_info {{
        background-color: {ColorScheme.PRIMARY_COLOR};
        color: white;
    }}

    QPushButton#closeButton {{
        background-color: transparent;
        color: white;
        border: none;
        font-weight: bold;
        padding: 4px;
    }}

    QPushButton#closeButton:hover {{
        background-color: rgba(255, 255, 255, 0.2);
    }}

    QLabel#notificationTitle {{
        font-weight: bold;
        font-size: 11pt;
        color: white;
    }}

    QLabel#notificationMessage {{
        color: white;
    }}
    """


def get_settings_style(theme="light"):
    """Get settings dialog style.

    Args:
        theme: "light" or "dark"

    Returns:
        Style sheet string
    """
    # Выбираем цветовую схему в зависимости от темы
    colors = ColorScheme.Light if theme == "light" else ColorScheme.Dark

    return f"""
    QDialog {{
        background-color: {colors.BACKGROUND_COLOR};
    }}

    QLabel#sectionTitle {{
        font-weight: bold;
        font-size: 12pt;
        color: {ColorScheme.PRIMARY_COLOR};
        margin-top: 12px;
    }}

    QLabel#fieldLabel {{
        font-weight: bold;
        color: {colors.TEXT_COLOR};
    }}

    QLineEdit#tokenField {{
        font-family: monospace;
        background-color: {colors.CARD_BACKGROUND};
        color: {colors.TEXT_COLOR};
    }}

    QLabel#validLabel {{
        color: {ColorScheme.SUCCESS_COLOR};
        font-weight: bold;
    }}

    QLabel#invalidLabel {{
        color: {ColorScheme.ERROR_COLOR};
        font-weight: bold;
    }}

    QPushButton#testButton {{
        padding: 4px 8px;
    }}
    
    QPushButton#fullWidthButton {{
        width: 100%;
    }}
    
    QFrame#titleBar {{
        background-color: {colors.HEADER_COLOR};
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    
    QPushButton#windowButton {{
        background-color: transparent;
        color: {colors.TEXT_COLOR};
        border: none;
        padding: 4px;
        border-radius: 2px;
        min-width: 20px;
        min-height: 20px;
        max-width: 20px;
        max-height: 20px;
    }}
    
    QPushButton#closeButton {{
        background-color: transparent;
        color: {colors.TEXT_COLOR};
        border: none;
        padding: 4px;
        border-radius: 2px;
        min-width: 20px;
        min-height: 20px;
        max-width: 20px;
        max-height: 20px;
    }}
    
    QPushButton#closeButton:hover {{
        background-color: {ColorScheme.ERROR_COLOR};
        color: white;
    }}
    
    QPushButton#windowButton:hover {{
        background-color: {colors.HOVER_COLOR};
    }}
    
    QLabel#windowTitle {{
        font-weight: bold;
        color: {colors.TEXT_COLOR};
    }}
    """


def get_payment_style(theme="light"):
    """Get payment widget style.

    Args:
        theme: "light" or "dark"

    Returns:
        Style sheet string
    """
    # Выбираем цветовую схему в зависимости от темы
    colors = ColorScheme.Light if theme == "light" else ColorScheme.Dark

    return f"""
    QWidget#paymentListContainer {{
        background-color: {colors.CARD_BACKGROUND};
    }}
    
    QScrollArea {{
        background-color: {colors.CARD_BACKGROUND};
        border: none;
    }}
    
    QFrame#paymentItem {{
        background-color: {colors.CARD_BACKGROUND};
        border-radius: 6px;
        border: 1px solid {colors.BORDER_COLOR};
    }}

    QLabel#amountLabel {{
        font-weight: bold;
        color: {ColorScheme.PRIMARY_COLOR};
        font-size: 12pt;
    }}

    QLabel#usernameLabel {{
        font-weight: bold;
        color: {colors.TEXT_COLOR};
    }}

    QLabel#dateLabel {{
        color: {colors.SECONDARY_TEXT_COLOR};
        font-size: 9pt;
    }}

    QLabel#commentLabel {{
        color: {colors.TEXT_COLOR};
        font-style: italic;
    }}
    """
