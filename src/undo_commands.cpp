// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#include "undo_commands.h"

#include "graphics_view.h"

MoveCommand::MoveCommand(const QList<QGraphicsItem*> &item_list, const QList<QPointF> &old, QUndoCommand *parent): QUndoCommand(parent) {
	items = item_list;
	old_positions = old;
	for (int i = 0; i < items.size(); ++i) {
		QGraphicsItem *item = items[i];
		new_positions.append(item->pos());
	}
}

void MoveCommand::undo() {
	for (int i = 0; i < items.size(); ++i) {
		QGraphicsItem *item = items[i];
		const QPointF old_position = old_positions[i];
		item->setPos(old_position);
	}
}

void MoveCommand::redo() {
	for (int i = 0; i < items.size(); ++i) {
		QGraphicsItem *item = items[i];
		const QPointF new_position = new_positions[i];
		item->setPos(new_position);
	}
}

DeleteCommand::DeleteCommand(GraphicsView *v, QUndoCommand *parent): QUndoCommand(parent) {
	view = v;
	scene = v->scene();
	items = scene->selectedItems();
	for (int i = 0; i < items.size(); ++i) {
		QGraphicsItem *item = items[i];
		item->setData(GraphicsItem::ItemIsDeleted, true);
		item->setSelected(false);
		item->hide();
	}
}

void DeleteCommand::undo() {
	for (int i = 0; i < items.size(); ++i) {
		QGraphicsItem *item = items[i];
		item->setData(GraphicsItem::ItemIsDeleted, false);
		item->show();
		item->setParentItem(view->image_layer);
	}
}

void DeleteCommand::redo() {
	for (int i = 0; i < items.size(); ++i) {
		QGraphicsItem *item = items[i];
		item->setData(GraphicsItem::ItemIsDeleted, true);
		item->hide();
	}
}
