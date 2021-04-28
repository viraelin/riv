// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#pragma once

#include <QApplication>
#include <QWidget>
#include <QGraphicsScene>
#include <QGraphicsItemGroup>
#include <QGraphicsRectItem>
#include <QGraphicsView>
#include <QProgressBar>
#include <QMouseEvent>
#include <QWheelEvent>
#include <QKeyEvent>
#include <QDragMoveEvent>
#include <QDragEnterEvent>
#include <QDropEvent>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QGraphicsColorizeEffect>
#include <QMimeType>
#include <QMimeDatabase>
#include <QMimeData>
#include <QFile>
#include <QFileDialog>
#include <QFileInfo>
#include <QTemporaryFile>
#include <QUrl>
#include <QNetworkReply>
#include <QStandardPaths>
#include <QSaveFile>
#include <QDataStream>

#include "graphics_item.h"

class GraphicsView: public QGraphicsView {

	Q_OBJECT

	public:
		QGraphicsColorizeEffect *effect = nullptr;
		QString current_project_path = "";
		QString project_filter = "RIV (*.riv)";
		const QString default_project_name = "untitled.riv";
		QGraphicsRectItem *image_layer = nullptr;
		bool has_scene_been_modified = false;
		QProgressBar *progress_bar = nullptr;
		QList<QGraphicsItem*> moving_items;
		QList<QPointF> moving_items_old_positions;
		QGraphicsRectItem *bounding_rect_item = nullptr;
		Qt::TransformationMode transformation_mode = Qt::TransformationMode::SmoothTransformation;

		GraphicsView(QGraphicsScene *scene, QWidget *parent = nullptr);
		void projectSave();
		void projectLoad(QString project_path = "");
		GraphicsItem *createItem(const QString &path, const QPointF &pos, const bool is_flipped = false, const qreal scale = 1.0, const qreal z_value = 0);
		void createItems(const QList<QString> &paths, const QPointF &origin);
		bool checkMimeData(const QString &path);
		void packSelection(const QPointF &origin);
		void selectAll();
		void clearCanvas();
		void showProgressBar(const qsizetype &item_count);
		void setBoundingRect();
		void updateSceneSize();

	protected:
		void mousePressEvent(QMouseEvent *event);
		void mouseReleaseEvent(QMouseEvent *event);
		void mouseMoveEvent(QMouseEvent *event);
		void wheelEvent(QWheelEvent *event);
		void keyPressEvent(QKeyEvent *event);
		void keyReleaseEvent(QKeyEvent *event);
		void dragMoveEvent(QDragMoveEvent *event);
		void dragEnterEvent(QDragEnterEvent *event);
		void dropEvent(QDropEvent *event);

	private:
		enum State {StateDefault, StatePan, StateResize};
		State state = StateDefault;
		QPointF resize_origin;
		QPointF mouse_last_resize_position;
		QPointF mouse_last_pan_position;
		QPointF mouse_last_drop_position;
		QNetworkAccessManager *network_manager = nullptr;
		
		void panView(QMouseEvent *event);
		void zoomView(QWheelEvent *event);
		void resizeSelection(QMouseEvent *event);
		void setState(const State s);
		void setItemParents(const QList<QGraphicsItem*> &items);
		void sendToFront(QGraphicsItem *item);

	signals:
		void itemMoved(const QList<QGraphicsItem*> &items, const QList<QPointF> &old_positions);

	public slots:
		void onNetworkReplyProgress(qint64 bytes_received, qint64 bytes_total);
		void onNetworkReplyFinished(QNetworkReply *reply);
};
