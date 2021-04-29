// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#include <QApplication>

#include "main_window.h"

int main(int argc, char *argv[]) {
	QApplication app(argc, argv);
	const QString name = "riv";
	const QString display_name = "Reference Image Viewer";
	app.setOrganizationName(name);
	app.setApplicationName(name);
	app.setApplicationDisplayName(display_name);
	MainWindow window;
	return app.exec();
}
