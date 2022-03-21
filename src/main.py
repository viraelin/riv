# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

from PyQt6.QtWidgets import QApplication

from main_window import MainWindow


def main():
    app = QApplication([])
    name = "riv"
    display_name = "Reference Image Viewer"
    app.setOrganizationName(name)
    app.setApplicationName(name)
    app.setApplicationDisplayName(display_name)
    window = MainWindow()
    return app.exec()


if __name__ == "__main__":
    main()

