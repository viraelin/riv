// Copyright (C) 2020 viraelin
// License: GPLv3.0-or-later

#pragma once

#include <QGraphicsScene>
#include <QGraphicsItem>
#include <QUndoCommand>

class GraphicsView;

class MoveCommand: public QUndoCommand {
	public:
		MoveCommand(const QList<QGraphicsItem*> &item_list, const QList<QPointF> &old, QUndoCommand *parent = nullptr);

		void undo() override;
		void redo() override;

	private:
		QList<QGraphicsItem*> items;
		QList<QPointF> old_positions;
		QList<QPointF> new_positions;
};

class DeleteCommand: public QUndoCommand {
	public:
		explicit DeleteCommand(GraphicsView *v, QUndoCommand *parent = nullptr);

		void undo() override;
		void redo() override;

	private:
		GraphicsView *view = nullptr;
		QGraphicsScene *scene = nullptr;
		QList<QGraphicsItem*> items;
};
