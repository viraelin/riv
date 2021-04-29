// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#include "graphics_view.h"

GraphicsView::GraphicsView(QGraphicsScene *scene, QWidget *parent): QGraphicsView(scene, parent) {
	progress_bar = new QProgressBar(this);
	effect = new QGraphicsColorizeEffect(this);
	network_manager = new QNetworkAccessManager(this);
	image_layer = new QGraphicsRectItem;

	connect(network_manager, &QNetworkAccessManager::finished, this, &GraphicsView::onNetworkReplyFinished);

	setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
	setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
	setAcceptDrops(true);
	setDragMode(DragMode::RubberBandDrag);
	setStyleSheet("background-color: #100111111;");
	setTransformationAnchor(NoAnchor);

	progress_bar->reset();
	progress_bar->setMinimum(0);
	progress_bar->hide();

	QPen pen;
	pen.setStyle(Qt::NoPen);
	QBrush brush = QBrush(QColor("#222222"));
	brush.setStyle(Qt::SolidPattern);
	bounding_rect_item = scene->addRect(QRectF(), pen, brush);
	bounding_rect_item->setZValue(-100);

	effect->setColor(QColor(0, 0, 0));
	effect->setEnabled(false);
	setGraphicsEffect(effect);

	scene->addItem(image_layer);
}

void GraphicsView::projectSave() {
	if (!parentWidget()->isWindowModified()) {
		return;
	}

	QString project_path = current_project_path;
	if (project_path.isEmpty()) {
		const QString path = QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation);
		const QString file_name = QFileDialog::getSaveFileName(
			parentWidget(),
			"Save Project",
			QDir(path).filePath(default_project_name),
			project_filter
		);

		if (file_name.isEmpty()) {
			qDebug() << "Save cancelled or no directory given" << file_name;
			return;
		}
		
		else {
			project_path = file_name;
		}
	}

	QSaveFile file(project_path);
	if (file.open(QIODevice::WriteOnly)) {
		QDataStream out(&file);
		const QList<QGraphicsItem*> items = image_layer->childItems();

		// project settings
		const int version = 100;
		const QPoint view_position = mapToScene(rect().center()).toPoint();
		const qreal zoom = transform().m11();
		const qsizetype item_count = items.size();

		out << version;
		out << view_position;
		out << item_count;
		out << zoom;

		showProgressBar(item_count);

		// save items
		for (int i = 0; i < items.size(); ++i) {
			GraphicsItem *item = static_cast<GraphicsItem*>(items[i]);

			const QPixmap pixmap = item->pixmap();
			QString path = item->data(GraphicsItem::ItemPath).toString();
			const bool is_flipped = item->data(GraphicsItem::ItemIsFlipped).toBool();
			// if zoomed in really far narrowing could matter
			const QPoint position = item->pos().toPoint();
			const qreal scale = item->sceneTransform().m11();
			const qreal z_value = item->zValue();

			if (item->data(GraphicsItem::ItemIsDeleted).toBool()) {
				delete item;
				continue;
			}

			out << path;
			out << pixmap;
			out << is_flipped;
			out << position;
			out << scale;
			out << z_value;

			progress_bar->setValue(i * 100);
			qApp->processEvents();
		}

		progress_bar->hide();
		current_project_path = project_path;
		file.commit();
	}

	else {
		qDebug() << "failed to open save file:" << project_path;
	}
}

void GraphicsView::projectLoad(QString project_path) {
	// default argument workaround
	if (project_path.isEmpty()) {
		project_path = current_project_path;
	}

	QFile file(project_path);
	if (file.open(QIODevice::ReadOnly)) {
		QDataStream in(&file);

		int version;
		QPoint view_position;
		qsizetype item_count;
		qreal zoom;

		in >> version;
		in >> view_position;
		in >> item_count;
		in >> zoom;

		// todo
		if (version != 100) {
			qDebug() << "error: file version invalid:" << version;
			return;
		}

		clearCanvas();
		showProgressBar(item_count);

		const qreal default_scale = 1.0/transform().m11();
		scale(default_scale, default_scale);
		scale(zoom, zoom);

		for (int i = 0; i < item_count; ++i) {
			QString path;
			in >> path;

			if (path.isEmpty()) { continue; }
			// if (!QFile::exists(path)) { continue; }

			QPixmap pixmap;
			bool is_flipped;
			QPoint position;
			qreal scale;
			qreal z_value;

			in >> pixmap;
			in >> is_flipped;
			in >> position;
			in >> scale;
			in >> z_value;

			// todo: merge with createItem or args for GraphicsItem
			GraphicsItem *item = new GraphicsItem(pixmap);
			item->setData(GraphicsItem::ItemPath, path);
			item->setData(GraphicsItem::ItemIsDeleted, false);
			item->setData(GraphicsItem::ItemIsFlipped, false);
			item->setPos(position);
			item->setScale(scale);
			item->setZValue(z_value);
			item->setTransformationMode(transformation_mode);

			if (is_flipped) { item->flip(); };

			item->setParentItem(image_layer);

			progress_bar->setValue(i * 100);
			qApp->processEvents();
		}

		setBoundingRect();
		centerOn(view_position);

		current_project_path = project_path;
		progress_bar->hide();
		file.close();

		QFileInfo info(project_path);
		parentWidget()->setWindowTitle(info.fileName() + "[*]");
	}

	else {
		qDebug() << "failed to open save file:" << project_path;
	}
}

void GraphicsView::mousePressEvent(QMouseEvent *event) {
	if (state == StateDefault) {
		if (event->button() == Qt::LeftButton) {
			QGraphicsView::mousePressEvent(event);
			moving_items = scene()->selectedItems();
			if (moving_items.size() > 0) {
				for (int i = 0; i < moving_items.size(); ++i) {
					QGraphicsItem *item = moving_items[i];
					sendToFront(item);
					moving_items_old_positions.append(item->pos());
				}
			}
		}

		else if (event->button() == Qt::MiddleButton) {
			mouse_last_pan_position = event->position();
			setState(StatePan);
		}
	}

	else if (state == StatePan) {
		if (event->button() == Qt::LeftButton) {
			mouse_last_pan_position = event->position();
		}

		else if (event->button() == Qt::MiddleButton) {
			mouse_last_pan_position = event->position();
		}
	}

	else if (state == StateResize) {
		if (event->button() == Qt::LeftButton) {
			mouse_last_resize_position = event->position();
			const QList<QGraphicsItem*> items = scene()->selectedItems();
			QGraphicsItemGroup *group = scene()->createItemGroup(items);
			resize_origin = group->childrenBoundingRect().center();
			scene()->destroyItemGroup(group);
			setItemParents(items);
		}
	}
}

void GraphicsView::mouseReleaseEvent(QMouseEvent *event) {
	if (state == StateDefault) {
		if (event->button() == Qt::LeftButton) {
			QGraphicsView::mouseReleaseEvent(event);
			if (moving_items.size() > 0) {
				emit itemMoved(moving_items, moving_items_old_positions);
				moving_items.clear();
				moving_items_old_positions.clear();
			}
			setBoundingRect();
		}
	}

	else if (state == StatePan) {
		if (event->button() == Qt::LeftButton) {
			setCursor(Qt::OpenHandCursor);
		}

		else if (event->button() == Qt::MiddleButton) {
			setState(StateDefault);
		}
	}
}

void GraphicsView::mouseMoveEvent(QMouseEvent *event) {
	if (state == StateDefault) {
		QGraphicsView::mouseMoveEvent(event);
		if (moving_items.size() > 0) {
			for (int i = 0; i < moving_items.size(); ++i) {
				QGraphicsItem *item = moving_items[i];
				sendToFront(item);
			}
		}
	}

	else if (state == StatePan) {
		if (event->buttons() == Qt::LeftButton) {
			panView(event);
		}

		else if (event->buttons() == Qt::MiddleButton) {
			panView(event);
		}
	}

	else if (state == StateResize) {
		if (event->buttons() == Qt::LeftButton) {
			resizeSelection(event);
		}
	}
}

void GraphicsView::keyPressEvent(QKeyEvent *event) {
	if (state == StateDefault) {
		if (event->key() == Qt::Key_Space && !event->isAutoRepeat()) {
			setState(StatePan);
		}

		else if (event->key() == Qt::Key_Control && !event->isAutoRepeat()) {
			setState(StateResize);
		}
	}
}

void GraphicsView::keyReleaseEvent(QKeyEvent *event) {
	if (state == StatePan) {
		if (event->key() == Qt::Key_Space && !event->isAutoRepeat()) {
			setState(StateDefault);
		}
	}

	else if (state == StateResize) {
		if (event->key() == Qt::Key_Control && !event->isAutoRepeat()) {
			setState(StateDefault);
		}
	}
}

void GraphicsView::wheelEvent(QWheelEvent *event) {
	zoomView(event);
}

// required
void GraphicsView::dragMoveEvent(QDragMoveEvent *event) {
	Q_UNUSED(event);
	return;
}

void GraphicsView::dragEnterEvent(QDragEnterEvent *event) {
	event->accept();
}

void GraphicsView::dropEvent(QDropEvent *event) {
	mouse_last_drop_position = mapToScene(event->position().toPoint());

	const QList<QUrl> urls = event->mimeData()->urls();
	QList<QString> paths;

	for (int i = 0; i < urls.size(); ++i) {
		const QUrl url = urls[i];
		const QString path = url.toLocalFile();
		if (checkMimeData(path)) {
			paths.append(path);
		}

		else {
			QNetworkRequest request(url);
			QNetworkReply *reply = network_manager->get(request);
			connect(reply, &QNetworkReply::downloadProgress, this, &GraphicsView::onNetworkReplyProgress);
		}
	}

	if (paths.size() > 0) {
		createItems(paths, mouse_last_drop_position);
	}
}

void GraphicsView::setBoundingRect() {
	updateSceneSize();
	QRectF new_rect = image_layer->childrenBoundingRect();
	bounding_rect_item->setRect(new_rect);
}

GraphicsItem *GraphicsView::createItem(const QString &path, const QPointF &pos, const bool is_flipped, const qreal scale, const qreal z_value) {
	GraphicsItem *item = new GraphicsItem(QPixmap(path));
	item->setData(GraphicsItem::ItemPath, path);
	item->setData(GraphicsItem::ItemIsFlipped, false);
	item->setPos(pos);
	item->setScale(scale);
	item->setZValue(z_value);
	item->setTransformationMode(transformation_mode);

	if (is_flipped) {
		item->flip();
	}

	item->setParentItem(image_layer);
	update();
	return item;
}

void GraphicsView::createItems(const QList<QString> &paths, const QPointF &origin) {
	scene()->clearSelection();
	const qsizetype item_count = paths.size();
	showProgressBar(item_count);

	for (int i = 0; i < item_count; ++i) {
		const QString path = paths[i];
		GraphicsItem *item = createItem(path, origin);
		item->setSelected(true);
		progress_bar->setValue(i * 100);
		qApp->processEvents();
	}

	progress_bar->hide();
	packSelection(origin);
}

bool GraphicsView::checkMimeData(const QString &path) {
	const QMimeType mimetype = QMimeDatabase().mimeTypeForFile(path);
	if (mimetype.name().startsWith("image")) {
		return true;
	}

	else {
		return false;
	}
}

void GraphicsView::onNetworkReplyProgress(qint64 bytes_received, qint64 bytes_total) {
	// hack
	const qreal percent = (qreal) bytes_received / (qreal) bytes_total;
	const int value = (percent * 100.0) * 100;
	const int count = 10000;
	showProgressBar(count);
	progress_bar->setValue(value);
}

void GraphicsView::onNetworkReplyFinished(QNetworkReply *reply) {
	// some requests fail: no redirect, no error
	progress_bar->hide();
	const QString temp = QDir::temp().filePath("XXXXXXXX-" + reply->url().fileName());
	QTemporaryFile file(temp);
	qDebug() << file.fileName();
	const QString file_name = file.fileName();

	if (file.open()) {
		qDebug() << file.fileName();
		file.write(reply->readAll());
		file.close();

		if (checkMimeData(file_name)) {
			createItem(file_name, mouse_last_drop_position);
		}
	}
}

void GraphicsView::panView(QMouseEvent *event) {
	updateSceneSize();
	setCursor(Qt::ClosedHandCursor);
	QPointF old_pos = mapToScene(mouse_last_pan_position.toPoint());
	QPointF new_pos = mapToScene(event->position().toPoint());
	QPointF delta = new_pos - old_pos;
	translate(delta.x(), delta.y());
	mouse_last_pan_position = event->position();
}

void GraphicsView::zoomView(QWheelEvent *event) {
	updateSceneSize();
	const QPoint pos = event->position().toPoint();
	const QPointF old_pos = mapToScene(pos);
	const int angle = event->angleDelta().y();
	qreal factor;
	const qreal zoom_in_factor = 1.2;
	const qreal zoom_out_factor = 1.0 / zoom_in_factor;
	factor = (angle > 0.0) ? zoom_in_factor : zoom_out_factor;
	scale(factor, factor);
	const QPointF new_pos = mapToScene(pos);
	const QPointF delta = new_pos - old_pos;
	translate(delta.x(), delta.y());
	setBoundingRect();
}

void GraphicsView::resizeSelection(QMouseEvent *event) {
	const QList<QGraphicsItem*> items = scene()->selectedItems();
	if (items.size() > 0) {
		QGraphicsItemGroup *group = scene()->createItemGroup(items);

		const QPointF epos = event->position();
		const QPointF delta = mouse_last_resize_position - epos;

		const qreal n = -delta.x();
		const int sign = (n > 0) - (n < 0);

		const qreal scene_scale = 1.0/transform().m11();
		const qreal zoom_scale = 0.001 * sign;

		const qreal current_scale = group->scale();
		qreal scale = current_scale + (delta.manhattanLength() * scene_scale) * zoom_scale;
		scale = std::max(scale, 0.01 * scene_scale);
		group->setTransformOriginPoint(resize_origin);
		group->setScale(scale);
		mouse_last_resize_position = epos;
		scene()->destroyItemGroup(group);
		setItemParents(items);
	}
}

void GraphicsView::setState(const State s) {
	if (s == state) {
		return;
	}

	if (s == StateDefault) {
		setCursor(Qt::ArrowCursor);
		setDragMode(DragMode::RubberBandDrag);
	}

	else if (s == StatePan) {
		setCursor(Qt::OpenHandCursor);
		setDragMode(DragMode::NoDrag);
	}

	else if (s == StateResize) {
		setCursor(Qt::SizeHorCursor);
		setDragMode(DragMode::NoDrag);
	}

	state = s;
}

void GraphicsView::setItemParents(const QList<QGraphicsItem*> &items) {
	// hack to try to prevent loss when switching item group
	// use plain rect item as parent because still allows canvas interaction
	for (int i = 0; i < items.size(); ++i) {
		QGraphicsItem *item = items[i];
		item->setParentItem(image_layer);
	}
}

void GraphicsView::packSelection(const QPointF &origin) {
	// simple row packing
	QList<QGraphicsItem*> items = scene()->selectedItems();

	qreal area = 0.0;
	qreal max_width = 0.0;

	for (int i = 0; i < items.size(); ++i) {
		GraphicsItem *item = static_cast<GraphicsItem*>(items[i]);
		qreal scale = item->sceneTransform().m11();
		area += (item->pixmap().width() * scale) * (item->pixmap().height() * scale);
		max_width = std::max(max_width, item->pixmap().width() * scale);
	}

	max_width *= 2.0;

	auto sortByHeight([](QGraphicsItem *_a, QGraphicsItem *_b) {
		GraphicsItem *a = static_cast<GraphicsItem*>(_a);
		GraphicsItem *b = static_cast<GraphicsItem*>(_b);
		const qreal as = a->sceneTransform().m11();
		const qreal bs = b->sceneTransform().m11();
		return (a->pixmap().height() * as) > (b->pixmap().height() * bs);
	});

	std::sort(items.begin(), items.end(), sortByHeight);

	int x = 0;
	int y = 0;
	int largest_height_this_row = 0;

	for (int i = 0; i < items.size(); ++i) {
		GraphicsItem *item = static_cast<GraphicsItem*>(items[i]);
		const QPixmap pixmap = item->pixmap();
		const qreal scale = item->sceneTransform().m11();
		const qreal width = pixmap.width() * scale;
		const qreal height = pixmap.height() * scale;

		// if outside max width, start new row
		if ((x + height) > max_width) {
			x = 0;
			y += largest_height_this_row;
			largest_height_this_row = 0;
		}

		// adjusted position
		const QPointF p(origin.x() + (x - max_width), origin.y() + (y - max_width));
		item->setPos(p);

		x += width;

		if (height > largest_height_this_row) {
			largest_height_this_row = height;
		}
	}
}

void GraphicsView::showProgressBar(const qsizetype &item_count) {
	if (item_count > 0) {
		// set progress bar to center
		// geometry is only correct if window is shown
		const QRect geometry_view = geometry();
		QRect geometry_progress_bar = progress_bar->geometry();
		geometry_progress_bar.moveCenter(geometry_view.center());
		progress_bar->setGeometry(geometry_progress_bar);
		progress_bar->reset();
		progress_bar->show();
		progress_bar->setMaximum((item_count * 100) - 100);
	}
}

void GraphicsView::selectAll() {
	const QList<QGraphicsItem*> items = image_layer->childItems();
	for (int i = 0; i < items.size(); ++i) {
		QGraphicsItem *item = items[i];
		item->setSelected(true);
	}
}

void GraphicsView::clearCanvas() {
	const QList<QGraphicsItem*> current_items = image_layer->childItems();
	for (int i = 0; i < current_items.size(); ++i) {
		QGraphicsItem *item = current_items[i];
		scene()->removeItem(item);
		delete item;
	}
}

void GraphicsView::updateSceneSize() {
	// bypass scrollbar scene size restrictions
	const int pad = 16000;
	const QRectF widget_rect_in_scene(mapToScene(-pad, -pad), mapToScene(rect().bottomRight() + QPoint(pad, pad)));
	QPointF new_top_left(sceneRect().topLeft());
	QPointF new_bottom_right(sceneRect().bottomRight());

	if (sceneRect().top() > widget_rect_in_scene.top()) {
		new_top_left.setY(widget_rect_in_scene.top());
	}

	if (sceneRect().bottom() < widget_rect_in_scene.bottom()) {
		new_bottom_right.setY(widget_rect_in_scene.bottom());
	}

	if (sceneRect().left() > widget_rect_in_scene.left()) {
		new_top_left.setX(widget_rect_in_scene.left());
	}

	if (sceneRect().right() < widget_rect_in_scene.right()) {
		new_bottom_right.setX(widget_rect_in_scene.right());
	}

	setSceneRect(QRectF(new_top_left, new_bottom_right));
}

void GraphicsView::sendToFront(QGraphicsItem *item) {
	qreal max_z = 0;
	const QList<QGraphicsItem*> colliding_items = item->collidingItems(Qt::IntersectsItemBoundingRect);
	for (int i = 0; i < colliding_items.size(); ++i) {
		QGraphicsItem *colliding_item = colliding_items[i];
		if (colliding_item == bounding_rect_item) { continue; }
		max_z = qMax(max_z, colliding_item->zValue());
	}
	item->setZValue(max_z + 1);
}
