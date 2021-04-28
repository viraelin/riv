// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#include "graphics_item.h"

GraphicsItem::GraphicsItem(const QPixmap &pixmap, QGraphicsItem *parent): QGraphicsPixmapItem(pixmap, parent) {
	setFlags(ItemIsMovable | ItemIsSelectable);
	setShapeMode(BoundingRectShape);
}

void GraphicsItem::flip() {
	QPixmap mirror = pixmap().transformed(QTransform().scale(-1, 1));
	setPixmap(mirror);
	setData(ItemIsFlipped, !data(ItemIsFlipped).toBool());
}

void GraphicsItem::paint(QPainter *painter, const QStyleOptionGraphicsItem *option, QWidget *widget) {
	int width = 1;
	QColor color(Qt::black);

	if (isSelected()) {
		// override selection border
		QStyleOptionGraphicsItem custom_option(*option);
		custom_option.state = QStyle::State_None;
		QGraphicsPixmapItem::paint(painter, &custom_option, widget);
		width = 2;
		color = QColor("#33CCCC");
	}

	else {
		QGraphicsPixmapItem::paint(painter, option, widget);
	}

	QRectF rect = boundingRect();
	QPen pen;
	pen.setWidth(width);
	pen.setCosmetic(true);
	pen.setJoinStyle(Qt::PenJoinStyle::MiterJoin);
	pen.setColor(color);

	painter->setRenderHint(QPainter::Antialiasing);
	painter->setPen(pen);
	painter->drawRect(rect);
}
