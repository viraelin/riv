// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#pragma once

#include <QApplication>
#include <QMainWindow>
#include <QGraphicsScene>
#include <QGraphicsItem>
#include <QMenu>
#include <QSettings>
#include <QAction>
#include <QWidgetAction>
#include <QContextMenuEvent>
#include <QCloseEvent>
#include <QWidget>
#include <QFileDialog>
#include <QStandardPaths>
#include <QToolButton>
#include <QHBoxLayout>
#include <QSlider>
#include <QUndoStack>

#include "graphics_view.h"
#include "undo_commands.h"

class MainWindow: public QMainWindow {

	public:
		MainWindow(QWidget *parent = nullptr);

	protected:
		void contextMenuEvent(QContextMenuEvent *event);
		void closeEvent(QCloseEvent *event);

	private:
		QGraphicsScene *scene = nullptr;
		GraphicsView *view = nullptr;
		QMenu *menu = nullptr;
		QSettings *settings = nullptr;
		QPoint menu_pos;

		// buttons (for ignore)
		QWidget *buttons = nullptr;
		QToolButton *button_restore = nullptr;
		QRect buttons_geometry;

		// settings gui
		QSlider *opacity_slider = nullptr;

		// menu
		QAction *delete_selection = nullptr;
		QAction *quit = nullptr;
		QAction *flip_selection = nullptr;
		QAction *project_new = nullptr;
		QAction *project_save = nullptr;
		QAction *project_save_as = nullptr;
		QAction *project_open = nullptr;
		QAction *import_images = nullptr;
		QAction *reset_view = nullptr;
		QAction *pack_selection = nullptr;
		QAction *select_all = nullptr;
		QAction *undo = nullptr;
		QAction *redo = nullptr;
		QAction *export_selection = nullptr;
		QWidgetAction *ignore_mouse = nullptr;
		QWidgetAction *grayscale = nullptr;
		QWidgetAction *bilinear_filtering = nullptr;
		QWidgetAction *always_on_top = nullptr;
		
		// undo
		QUndoStack *undo_stack = nullptr;

		void saveSettings();
		void loadSettings();
		void createMenuActions();

	public slots:
		void onGrayscaleToggled(const bool state);
		void onDeleteTriggered();
		void onQuitTriggered();
		void onFlipSelection();
		void onProjectNew();
		void onProjectSave();
		void onProjectOpen();
		void onOpenImages();
		void onResetView();
		void onIgnoreMouseToggled(const bool state);
		void onPackSelection();
		void onSelectAll();
		void onButtonRestoreClicked();
		void onOpacitySliderValueChanged(const int value);
		void onItemMoved(const QList<QGraphicsItem*> &items, const QList<QPointF> &old_positions);
		void onItemDeleted();
		void onBilinearFilteringToggled(const bool state);
		void onExportSelection();
		void onUndoStackCleanChanged(const bool is_clean);
		void onAlwaysOnTopToggled(const bool state);
		void onItemFlipped(const QList<QGraphicsItem*> &items);
};
