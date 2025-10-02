#!/usr/bin/env python3
"""
hsim Model Designer - Main entry point
Visual designer for discrete event simulation models
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from hsim.gui.views.main_window import MainWindow


def main():
    """Main entry point"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("hsim Model Designer")
    app.setOrganizationName("hsim")

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
