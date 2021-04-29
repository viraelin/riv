// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#include "main_window.h"

MainWindow::MainWindow(QWidget *parent): QMainWindow(parent) {
	scene = new QGraphicsScene(this);
	view = new GraphicsView(scene, this);
	menu = new QMenu(this);
	settings = new QSettings(this);
	undo_stack = new QUndoStack(this);
	undo_stack->setUndoLimit(50);

	connect(undo_stack, &QUndoStack::cleanChanged, this, &MainWindow::onUndoStackCleanChanged);
	connect(view, &GraphicsView::itemMoved, this, &MainWindow::onItemMoved);

	// buttons
	buttons = new QWidget;
	button_restore = new QToolButton;
	button_restore->setText("+");

	// settings gui
	opacity_slider = new QSlider(view);
	opacity_slider->setOrientation(Qt::Horizontal);
	opacity_slider->setMinimum(10);
	opacity_slider->setMaximum(100);
	opacity_slider->setValue(100);
	connect(opacity_slider, &QSlider::valueChanged, this, &MainWindow::onOpacitySliderValueChanged);

	QHBoxLayout	layout;
	layout.setSizeConstraint(QLayout::SetFixedSize);
	layout.setContentsMargins(0, 0, 0, 0);
	layout.addWidget(button_restore);
	buttons->setLayout(&layout);
	// workaround to get correct initial geometry
	buttons->show();
	buttons_geometry = buttons->geometry();
	buttons->hide();

	buttons->setStyleSheet("\
		background-color: #100111111;\
		color: #b2b2b2;\
	");

	buttons->setWindowFlags(
		Qt::FramelessWindowHint |
		Qt::NoDropShadowWindowHint |
		Qt::X11BypassWindowManagerHint |
		Qt::WindowStaysOnTopHint
	);

	connect(button_restore, &QToolButton::clicked, this, &MainWindow::onButtonRestoreClicked);

	QFileInfo info(view->current_project_path);
	setWindowTitle(QString("%1[*]").arg(info.fileName()));
	setAttribute(Qt::WA_TranslucentBackground, true);
	// setWindowFlags(Qt::FramelessWindowHint | Qt::NoDropShadowWindowHint);
	setCentralWidget(view);

	show();

	QFile file("src/stylesheet.qss");
	if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
		QByteArray data = file.readAll();
		setStyleSheet(data);
		file.close();
	}

	createMenuActions();
	loadSettings();
	view->projectLoad();
	undo_stack->setClean();
}

void MainWindow::contextMenuEvent(QContextMenuEvent *event) {
	if (scene->selectedItems().size() == 0) {
		delete_selection->setEnabled(false);
	}
	else {
		delete_selection->setEnabled(true);
	}

	menu->popup(view->mapToGlobal(event->pos()));
	delete_selection->setEnabled(true);

	// hack
	menu_pos = event->pos();
}

void MainWindow::closeEvent(QCloseEvent *event) {
	Q_UNUSED(event);
	saveSettings();
	view->projectSave();
}

void MainWindow::saveSettings() {
	settings->setValue("grayscale", grayscale->isChecked());
	settings->setValue("window_geometry", geometry());
	settings->setValue("project_path", view->current_project_path);
	settings->setValue("filter", bilinear_filtering->isChecked());
}

void MainWindow::loadSettings() {
	const QRect default_window_geometry = QRect(300, 100, 800, 600);
	const QRect window_geometry = settings->value("window_geometry", default_window_geometry).toRect();
	move(window_geometry.x(), window_geometry.y());
	resize(window_geometry.width(), window_geometry.height());

	const bool is_grayscale = settings->value("grayscale", false).toBool();
	grayscale->setChecked(is_grayscale);

	const QString project_path = settings->value("project_path", "").toString();
	view->current_project_path = project_path;

	const bool is_filtering = settings->value("filter").toBool();
	bilinear_filtering->setChecked(is_filtering);
	onBilinearFilteringToggled(is_filtering);
}

void MainWindow::onGrayscaleToggled(bool state) {
	view->effect->setEnabled(state);
}

void MainWindow::onQuitTriggered() {
	close();
}

void MainWindow::onFlipSelection() {
	QList<QGraphicsItem*> items = scene->selectedItems();
	undo_stack->push(new FlipCommand(items));
}

void MainWindow::onProjectNew() {
	onProjectSave();
	view->clearCanvas();
	view->current_project_path = "";
	undo_stack->resetClean();
	setWindowTitle(view->default_project_name + "[*]");
}

void MainWindow::onProjectSave() {
	saveSettings();
	view->projectSave();
	undo_stack->setClean();
}

void MainWindow::onProjectOpen() {
	const QString file_name = QFileDialog::getOpenFileName(
		this,
		"Open Project",
		QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation),
		view->project_filter
	);

	if (file_name.isEmpty()) {
		qDebug() << "Open project cancelled or no file name given";
		return;
	}

	else {
		view->projectLoad(file_name);
		undo_stack->setClean();
	}
}

void MainWindow::onOpenImages() {
	QString filter = "Images (*.jpg *.jpeg *.png)";
	const QList<QString> paths = QFileDialog::getOpenFileNames(
		this,
		"Open Images",
		QStandardPaths::writableLocation(QStandardPaths::PicturesLocation),
		filter,
		&filter
	);
	QList<QString> new_paths;

	for (int i = 0; i < paths.size(); ++i) {
		const QString path = paths[i];
		if (view->checkMimeData(path)) {
			new_paths.append(path);
		}
	}

	if (new_paths.size() > 0) {
		view->createItems(new_paths, menu_pos);
	}
}

void MainWindow::onExportSelection() {
	const QString directory = QFileDialog::getExistingDirectory(
		this,
		"Export Directory",
		QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation)
	);
	QList<QGraphicsItem*> items = scene->selectedItems();
	const qsizetype item_count = items.size();
	view->showProgressBar(item_count);
	for (int i = 0; i < items.size(); ++i) {
		GraphicsItem *item = static_cast<GraphicsItem*>(items[i]);
		QFileInfo info(item->data(GraphicsItem::ItemPath).toString());
		QString export_path = QDir(directory).filePath(info.fileName());
		const bool result = item->pixmap().save(export_path);
		if (!result) {
			qDebug() << "failed to save" << export_path;
		}
		view->progress_bar->setValue(i * 100);
		qApp->processEvents();
	}
	view->progress_bar->hide();
}

void MainWindow::onResetView() {
	view->setTransformationAnchor(QGraphicsView::AnchorViewCenter);
	view->centerOn(QPoint());
	view->resetTransform();
	view->setTransformationAnchor(QGraphicsView::NoAnchor);
}

void MainWindow::onIgnoreMouseToggled(const bool state) {
	// sets window transparent, allows click-through and adds a restore button
	const QRect geometry = qApp->primaryScreen()->geometry();
	QString sheet;

	buttons->setVisible(state);
	buttons->move(geometry.right() - buttons_geometry.width(), geometry.top() + buttons_geometry.height());

	if (state) {
		sheet = "background-color: #00111111";
	}

	else {
		sheet = "background-color: #100111111";
	}

	opacity_slider->setVisible(!state);
	view->setStyleSheet(sheet);
	view->bounding_rect_item->setVisible(!state);
	scene->clearSelection();

	setWindowFlag(Qt::WindowStaysOnTopHint, state);
	setWindowFlag(Qt::WindowTransparentForInput, state);
	setWindowFlag(Qt::X11BypassWindowManagerHint, state);
	show();
}

void MainWindow::onPackSelection() {
	const QPointF origin = view->mapToScene(mapFromGlobal(QCursor::pos()));
	view->packSelection(origin);
}

void MainWindow::onSelectAll() {
	view->selectAll();
}

void MainWindow::onButtonRestoreClicked() {
	ignore_mouse->setChecked(false);
	onIgnoreMouseToggled(false);
}

void MainWindow::onOpacitySliderValueChanged(const int value) {
	setWindowOpacity(value/100.0);
}

void MainWindow::onItemMoved(const QList<QGraphicsItem*> &items, const QList<QPointF> &old_positions) {
	undo_stack->push(new MoveCommand(items, old_positions));
}

void MainWindow::onItemDeleted() {
	undo_stack->push(new DeleteCommand(view));
}

void MainWindow::onBilinearFilteringToggled(const bool state) {
	if (state) {
		view->transformation_mode = Qt::TransformationMode::SmoothTransformation;
	}

	else {
		view->transformation_mode = Qt::TransformationMode::FastTransformation;
	}

	const QList<QGraphicsItem*> items = view->image_layer->childItems();
	if (items.size() > 0) {
		for (int i = 0; i < items.size(); ++i) {
			GraphicsItem *item = static_cast<GraphicsItem*>(items[i]);
			item->setTransformationMode(view->transformation_mode);
		}
	}
}

void MainWindow::onUndoStackCleanChanged(const bool is_clean) {
	setWindowModified(!is_clean);
}

void MainWindow::createMenuActions() {
	delete_selection = new QAction(this);
	quit = new QAction(this);
	flip_selection = new QAction(this);
	project_new = new QAction(this);
	project_save = new QAction(this);
	project_save_as = new QAction(this);
	project_open = new QAction(this);
	import_images = new QAction(this);
	reset_view = new QAction(this);
	ignore_mouse = new QWidgetAction(this);
	grayscale = new QWidgetAction(this);
	pack_selection = new QAction(this);
	select_all = new QAction(this);
	bilinear_filtering = new QWidgetAction(this);
	export_selection = new QAction(this);

	undo = undo_stack->createUndoAction(this);
	undo->setText("Undo");
	undo->setShortcut(QKeySequence::Undo);
	addAction(undo);

	redo = undo_stack->createRedoAction(this);
	redo->setText("Redo");
	redo->setShortcut(QKeySequence::Redo);
	addAction(redo);

	connect(delete_selection, &QAction::triggered, this, &MainWindow::onItemDeleted);
	connect(quit, &QAction::triggered, this, &MainWindow::onQuitTriggered);
	connect(grayscale, &QWidgetAction::toggled, this, &MainWindow::onGrayscaleToggled);
	connect(flip_selection, &QAction::triggered, this, &MainWindow::onFlipSelection);
	connect(project_new, &QAction::triggered, this, &MainWindow::onProjectNew);
	connect(project_save, &QAction::triggered, this, &MainWindow::onProjectSave);
	connect(project_open, &QAction::triggered, this, &MainWindow::onProjectOpen);
	connect(import_images, &QAction::triggered, this, &MainWindow::onOpenImages);
	connect(ignore_mouse, &QWidgetAction::toggled, this, &MainWindow::onIgnoreMouseToggled);
	connect(reset_view, &QAction::triggered, this, &MainWindow::onResetView);
	connect(pack_selection, &QAction::triggered, this, &MainWindow::onPackSelection);
	connect(select_all, &QAction::triggered, this, &MainWindow::onSelectAll);
	connect(bilinear_filtering, &QWidgetAction::toggled, this, &MainWindow::onBilinearFilteringToggled);
	connect(export_selection, &QAction::triggered, this, &MainWindow::onExportSelection);

	grayscale->setText("Grayscale");
	grayscale->setCheckable(true);
	grayscale->setShortcut(QKeySequence(Qt::Key_G));
	grayscale->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(grayscale);

	select_all->setText("Select All");
	select_all->setShortcut(QKeySequence::SelectAll);
	select_all->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(select_all);

	pack_selection->setText("Pack Selection");
	addAction(pack_selection);

	import_images->setText("Import Images");
	import_images->setShortcut(QKeySequence::Open);
	import_images->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(import_images);

	flip_selection->setText("Flip Selection");
	flip_selection->setShortcut(QKeySequence(Qt::Key_M));
	flip_selection->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(flip_selection);

	bilinear_filtering->setText("Bilinear Filtering");
	bilinear_filtering->setCheckable(true);
	addAction(bilinear_filtering);

	project_new->setText("New Project");
	project_new->setShortcut(QKeySequence::New);
	project_new->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(project_new);

	project_save->setText("Save Project");
	project_save->setShortcut(QKeySequence::Save);
	project_save->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(project_save);

	project_open->setText("Open Project");
	project_open->setShortcut(QKeySequence("Ctrl+Shift+O"));
	project_open->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(project_open);

	reset_view->setText("Reset View");
	addAction(reset_view);

	ignore_mouse->setText("Ignore Mouse");
	ignore_mouse->setCheckable(true);
	addAction(ignore_mouse);

	delete_selection->setText("Delete");
	delete_selection->setShortcut(QKeySequence::Delete);
	delete_selection->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(delete_selection);

	quit->setText("Quit");
	quit->setShortcut(QKeySequence::Quit);
	quit->setShortcutContext(Qt::ShortcutContext::ApplicationShortcut);
	addAction(quit);

	export_selection->setText("Export Selection");
	addAction(export_selection);

	menu->addAction(undo);
	menu->addAction(redo);
	menu->addSeparator();
	menu->addAction(grayscale);
	menu->addAction(bilinear_filtering);
	menu->addAction(ignore_mouse);
	menu->addSeparator();
	menu->addAction(select_all);
	menu->addAction(flip_selection);
	menu->addAction(pack_selection);
	menu->addAction(delete_selection);
	menu->addSeparator();
	menu->addAction(project_new);
	menu->addAction(project_save);
	menu->addAction(project_open);
	menu->addSeparator();
	menu->addAction(import_images);
	menu->addAction(export_selection);
	menu->addAction(reset_view);
	menu->addSeparator();
	menu->addAction(quit);
}