// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#pragma once

#include <QGraphicsPixmapItem>
#include <QPainter>
#include <QStyleOptionGraphicsItem>
#include <QGraphicsScene>
#include <QGraphicsView>
#include <QDataStream>

class GraphicsItem: public QGraphicsPixmapItem {
	public:
		enum Data {
			ItemPath,
			ItemIsFlipped,
			ItemIsDeleted
		};
		GraphicsItem() {};
		GraphicsItem &operator = (const GraphicsItem &other);
		GraphicsItem(const QPixmap &pixmap, QGraphicsItem *parent = nullptr);
		void flip();
		void paint(QPainter *painter, const QStyleOptionGraphicsItem *option, QWidget *widget);
};
