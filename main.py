"""
Main entry point for the LOLZTEAM DONATE application.

This script handles both GUI and console modes.
"""

import argparse
import sys

from PyQt5.QtGui import QIcon

from gui.resource_helper import resource_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LOLZTEAM DONATE - DonationAlerts Integration"
    )

    parser.add_argument(
        "--console", "-c",
        action="store_true",
        help="Run in console mode"
    )

    args = parser.parse_args()

    if args.console:
        # Run in console mode
        from console.cli import ConsoleInterface
        console = ConsoleInterface()
        console.run()
    else:
        # Run in GUI mode
        from PyQt5.QtWidgets import QApplication
        from gui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("LOLZTEAM DONATE")

        # Set app icon
        app_icon = QIcon(resource_path("gui/resources/icons/app_icon.ico"))
        app.setWindowIcon(app_icon)

        # Initialize main window
        main_window = MainWindow()

        # Set up async event loop integration
        import qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Start the event loop
        with loop:
            sys.exit(loop.run_forever())


if __name__ == "__main__":
    # Check for PyQt5
    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        print("Error: PyQt5 is required for GUI mode.")
        print("Please install it using: pip install PyQt5")
        print("Or run in console mode with: python main.py --console")
        sys.exit(1)

    # Check for asyncio
    try:
        import asyncio
    except ImportError:
        print("Error: asyncio is required.")
        print("Please install it using: pip install asyncio")
        sys.exit(1)

    main()
