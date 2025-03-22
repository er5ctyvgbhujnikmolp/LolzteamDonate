"""
Main entry point for the LOLZTEAM DONATE application.

This script handles both GUI and console modes.
"""

import argparse
import os
import sys

from PyQt5.QtGui import QIcon

# Create necessary package structure
package_dirs = [
    "config",
    "core",
    "gui",
    "gui/resources",
    "console"
]

for directory in package_dirs:
    os.makedirs(directory, exist_ok=True)

    # Create __init__.py files
    init_file = os.path.join(directory, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write(f'"""\n{directory.capitalize()} package for LOLZTEAM DONATE.\n"""\n')


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
        app_icon = QIcon("gui/resources/icons/app_icon.ico")  # Укажите путь к вашей иконке
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
