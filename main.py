"""
Main entry point for the LOLZTEAM DONATE application.

This script handles both GUI and console modes.
"""

import argparse
import sys

from PyQt5.QtGui import QIcon

from core.logging_setup import setup_logging
from core.single_instance import SingleInstanceChecker, AlreadyRunningDialog
from gui.resource_helper import resource_path


def main():
    """Main entry point."""
    # Set up logging
    logger = setup_logging()
    logger.info("LOLZTEAM DONATE starting...")

    # Parse command line arguments
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
        logger.info("Starting in console mode")
        console = ConsoleInterface()
        console.run()
    else:
        # Run in GUI mode
        from PyQt5.QtWidgets import QApplication

        app = QApplication(sys.argv)
        app.setApplicationName("LOLZTEAM DONATE")

        # Set app icon
        app_icon = QIcon(resource_path("gui/resources/icons/app_icon.ico"))
        app.setWindowIcon(app_icon)

        # Check if another instance is already running
        instance_checker = SingleInstanceChecker("lolzteam_donate")
        if not instance_checker.try_acquire_lock():
            logger.warning("Another instance is already running, showing dialog")
            dialog = AlreadyRunningDialog()
            dialog.exec_()
            return

        # Set up async event loop integration BEFORE creating the main window
        import qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Import main window only after checking instance to avoid unnecessary imports
        from gui.main_window import MainWindow

        # Initialize main window
        logger.info("Initializing main window")

        with loop:  # This ensures that the event loop is running when MainWindow is created
            main_window = MainWindow()
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

    # Check for httpx
    try:
        import httpx
    except ImportError:
        print("Error: httpx is required.")
        print("Please install it using: pip install httpx")
        sys.exit(1)

    # Check for qasync
    try:
        import qasync
    except ImportError:
        print("Error: qasync is required.")
        print("Please install it using: pip install qasync")
        sys.exit(1)

    main()