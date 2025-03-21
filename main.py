"""
Main entry point for the LOLZTEAM DONATE application.

This script handles both GUI and console modes.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

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
        # TODO: Add app icon

        # Initialize main window
        main_window = MainWindow()

        # Set up async event loop integration
        import qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Start the event loop
        with loop:
            sys.exit(loop.run_forever())


def initialize_sounds():
    """Инициализация директории звуков и создание базовых звуковых файлов."""
    sounds_dir = Path("sounds")
    sounds_dir.mkdir(exist_ok=True)

    # Проверка наличия звуковых файлов
    required_sounds = {
        "info.wav": "Информационное уведомление",
        "success.wav": "Успешное уведомление",
        "warning.wav": "Предупреждающее уведомление",
        "error.wav": "Уведомление об ошибке"
    }

    # Создание простых звуковых файлов, если их нет
    # В реальном приложении нужно добавить настоящие звуковые файлы
    # Этот код нужен только для примера
    for sound_file, description in required_sounds.items():
        sound_path = sounds_dir / sound_file
        if not sound_path.exists():
            try:
                # Для примера копируем один из стандартных системных звуков
                if os.name == "nt":  # Windows
                    system_sounds = {
                        "info.wav": "%SystemRoot%\\Media\\Windows Notify.wav",
                        "success.wav": "%SystemRoot%\\Media\\Windows Notify System Generic.wav",
                        "warning.wav": "%SystemRoot%\\Media\\Windows Exclamation.wav",
                        "error.wav": "%SystemRoot%\\Media\\Windows Critical Stop.wav"
                    }
                    system_sound = os.path.expandvars(system_sounds.get(sound_file, system_sounds["info.wav"]))
                    if os.path.exists(system_sound):
                        shutil.copy(system_sound, sound_path)
                    else:
                        print(f"Системный звук не найден: {system_sound}")
                else:  # Linux/Mac
                    # Создаем пустой звуковой файл
                    with open(sound_path, "wb") as f:
                        f.write(
                            b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
                    print(f"Создан пустой звуковой файл: {sound_path}")
            except Exception as e:
                print(f"Ошибка при создании звукового файла {sound_file}: {e}")


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

    initialize_sounds()
    main()
