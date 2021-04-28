// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#include <QApplication>

#include "main_window.h"

int main(int argc, char *argv[]) {
	QApplication app(argc, argv);
	QString name = "riv";
	app.setOrganizationName(name);
	app.setApplicationName(name);
	MainWindow window;
	return app.exec();
}
