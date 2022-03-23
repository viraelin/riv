# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from graphics_view import GraphicsView
from graphics_item import (GraphicsItem, GraphicsItemData)
from undo_commands import *


class MainWindow(QMainWindow):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self._scene = QGraphicsScene(self)
        self._view = GraphicsView(self._scene, self)
        self._menu = QMenu(self)
        self._settings = QSettings(self)
        self._undo_stack = QUndoStack(self)
        self._undo_stack.setUndoLimit(50)
        self._undo_stack.cleanChanged.connect(self.onUndoStackCleanChanged)
        self._view.itemMoved.connect(self.onItemMoved)
        self._menu_pos = QPointF()

        # menu
        self._delete_selection = QAction(self)
        self._quit = QAction(self)
        self._flip_selection = QAction(self)
        self._project_new = QAction(self)
        self._project_save = QAction(self)
        self._project_save_as = QAction(self)
        self._project_open = QAction(self)
        self._import_images = QAction(self)
        self._reset_view = QAction(self)
        self._pack_selection = QAction(self)
        self._select_all = QAction(self)
        self._undo = QAction(self)
        self._redo = QAction(self)
        self._export_selection = QAction(self)
        self._ignore_mouse = QWidgetAction(self)
        self._grayscale = QWidgetAction(self)
        self._bilinear_filtering = QWidgetAction(self)
        self._always_on_top = QWidgetAction(self)

        # buttons
        self._buttons = QWidget()
        self._button_restore = QToolButton()
        self._button_restore.setText("+")

        # settings gui
        self._opacity_slider = QSlider(self._view)
        self._opacity_slider.setOrientation(Qt.Orientation.Horizontal)
        self._opacity_slider.setMinimum(10)
        self._opacity_slider.setMaximum(100)
        self._opacity_slider.setValue(100)
        self._opacity_slider.valueChanged.connect(self.onOpacitySliderValueChanged)

        layout = QHBoxLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._button_restore)
        self._buttons.setLayout(layout)
        # workaround to get correct initial geometry
        self._buttons.show()
        self._buttons_geometry = self._buttons.geometry()
        self._buttons.hide()
        self._buttons.setStyleSheet("\
            background-color: #100111111;\
            color: #b2b2b2;\
        ")

        self._buttons.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint |
            Qt.WindowType.X11BypassWindowManagerHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self._button_restore.clicked.connect(self.onButtonRestoreClicked)
        info = QFileInfo(self._view.current_project_path)

        self.setWindowTitle(f"{info.fileName()}[*]")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setCentralWidget(self._view)

        self.show()

        stylesheet_path = "stylesheet.qss"
        with open(stylesheet_path, "r") as fp:
            data = fp.read()
            self.setStyleSheet(data)

        self.createMenuActions()
        self.loadSettings()
        if self._view.projectLoad():
            self._undo_stack.setClean()


    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if len(self._scene.selectedItems()) == 0:
            self._delete_selection.setEnabled(False)
        else:
            self._delete_selection.setEnabled(True)

        self._menu.popup(self._view.mapToGlobal(event.pos()))

        # hack
        self._menu_pos = QPointF(event.pos())


    def closeEvent(self, _event: QCloseEvent) -> None:
        self.saveSettings()
        self._view.projectSave()


    def saveSettings(self) -> None:
        self._settings.setValue("grayscale", self._grayscale.isChecked())
        self._settings.setValue("window_geometry", self.geometry())
        self._settings.setValue("project_path", self._view.current_project_path)
        self._settings.setValue("filter", self._bilinear_filtering.isChecked())


    def loadSettings(self) -> None:
        default_window_geometry = QRect(300, 100, 800, 600)
        window_geometry = self._settings.value("window_geometry", default_window_geometry, type=QRect)
        self.move(window_geometry.x(), window_geometry.y())
        self.resize(window_geometry.width(), window_geometry.height())

        is_grayscale = self._settings.value("grayscale", False, type=bool)
        self._grayscale.setChecked(is_grayscale)

        project_path = self._settings.value("project_path", "", type=str)
        self._view.current_project_path = project_path

        is_filtering = self._settings.value("filter", True, type=bool)
        self._bilinear_filtering.setChecked(is_filtering)
        self.onBilinearFilteringToggled(is_filtering)


    def onGrayscaleToggled(self, state: bool) -> None:
        self._view.effect.setEnabled(state)

    def onQuitTriggered(self) -> None:
        self.close()


    def onFlipSelection(self) -> None:
        items = self._scene.selectedItems()
        self._undo_stack.push(FlipCommand(items))


    def onProjectNew(self) -> None:
        self.onProjectSave()
        self._view.clearCanvas()
        self._view.current_project_path = ""
        self._undo_stack.resetClean()
        self.setWindowTitle(self._view.default_project_name + "[*]")


    def onProjectSave(self) -> None:
        self.saveSettings()
        if self._view.projectSave():
            self._undo_stack.setClean()


    def onProjectOpen(self) -> None:
        file_name, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            self._view.project_filter
        )

        if file_name != "":
            if self._view.projectLoad(file_name):
                self._undo_stack.setClean()
        else:
            return


    def onOpenImages(self) -> None:
        _filter = "Images (*.jpg *.jpeg *.png)"
        paths, _selected_filter = QFileDialog.getOpenFileNames(
            self,
            "Open Images",
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation),
            _filter,
            _filter
        )

        new_paths = []
        for path in paths:
            if self._view.checkMimeData(path):
                new_paths.append(path)

        if len(new_paths) > 0:
            self._view.createItems(new_paths, self._menu_pos)


    def onExportSelection(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Export Directory",
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        )

        items = self._scene.selectedItems()
        item_count = len(items)
        self._view.showProgressBar(item_count)
        for i in range(0, item_count):
            item = items[i]
            info = QFileInfo(item.data(GraphicsItemData.ItemPath.value))
            export_path = QDir(directory).filePath(info.fileName())
            result = item.pixmap().save(export_path)

            if not result:
                # todo
                pass

            self._view.updateProgressBar.emit(i)

        self._view.progress_bar.hide()


    def onResetView(self) -> None:
        self._view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._view.centerOn(QPointF())
        self._view.resetTransform()
        self._view.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)


    def onIgnoreMouseToggled(self, state: bool) -> None:
        # sets window transparent, allows click-through and adds a restore button
        geometry = QApplication.primaryScreen().geometry()
        sheet = ""

        self._buttons.setVisible(state)
        self._buttons.move(geometry.right() - self._buttons_geometry.width(), geometry.top() + self._buttons_geometry.height())

        if state:
            sheet = "background-color: #00111111"
        else:
            sheet = "background-color: #100111111"

        self._opacity_slider.setVisible(not state)
        self._view.setStyleSheet(sheet)
        self._view.bounding_rect_item.setVisible(not state)
        self._scene.clearSelection()

        if not self._always_on_top.isChecked():
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, state)

        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, state)
        self.setWindowFlag(Qt.WindowType.X11BypassWindowManagerHint, state)
        self.show()


    def onPackSelection(self) -> None:
        self._view.packSelection()


    def onSelectAll(self) -> None:
        self._view.selectAll()


    def onButtonRestoreClicked(self) -> None:
        self._ignore_mouse.setChecked(False)
        self.onIgnoreMouseToggled(False)


    def onOpacitySliderValueChanged(self, value: int) -> None:
        self.setWindowOpacity(float(value)/100.0)


    def onItemMoved(self, items: list, old_positions: list) -> None:
        self._undo_stack.push(MoveCommand(items, old_positions))


    def onItemDeleted(self) -> None:
        self._undo_stack.push(DeleteCommand(self._view))


    def onBilinearFilteringToggled(self, state: bool) -> None:
        if state:
            self._view.transformation_mode = Qt.TransformationMode.SmoothTransformation
        else:
            self._view.transformation_mode = Qt.TransformationMode.FastTransformation

        items = self._view.image_layer.childItems()
        if len(items) > 0:
            for item in items:
                item.setTransformationMode(self._view.transformation_mode)


    def onAlwaysOnTopToggled(self, state: bool) -> None:
        # required for linux
        self.setWindowFlag(Qt.WindowType.X11BypassWindowManagerHint, state)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, state)
        self.show()


    def onUndoStackCleanChanged(self, is_clean: bool) -> None:
        self.setWindowModified(not is_clean)


    def createMenuActions(self) -> None:
        self._undo = self._undo_stack.createUndoAction(self)
        self._undo.setText("Undo")
        self._undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.addAction(self._undo)

        self._redo = self._undo_stack.createRedoAction(self)
        self._redo.setText("Redo")
        self._redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.addAction(self._redo)

        self._delete_selection.triggered.connect(self.onItemDeleted)
        self._quit.triggered.connect(self.onQuitTriggered)
        self._grayscale.toggled.connect(self.onGrayscaleToggled)
        self._flip_selection.triggered.connect(self.onFlipSelection)
        self._project_new.triggered.connect(self.onProjectNew)
        self._project_save.triggered.connect(self.onProjectSave)
        self._project_open.triggered.connect(self.onProjectOpen)
        self._import_images.triggered.connect(self.onOpenImages)
        self._ignore_mouse.toggled.connect(self.onIgnoreMouseToggled)
        self._reset_view.triggered.connect(self.onResetView)
        self._pack_selection.triggered.connect(self.onPackSelection)
        self._select_all.triggered.connect(self.onSelectAll)
        self._bilinear_filtering.toggled.connect(self.onBilinearFilteringToggled)
        self._export_selection.triggered.connect(self.onExportSelection)
        self._always_on_top.toggled.connect(self.onAlwaysOnTopToggled)

        self._grayscale.setText("Grayscale")
        self._grayscale.setCheckable(True)
        self._grayscale.setShortcut(QKeySequence(Qt.Key.Key_G))
        self._grayscale.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._grayscale)

        self._select_all.setText("Select All")
        self._select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self._select_all.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._select_all)

        self._pack_selection.setText("Pack Selection")
        self.addAction(self._pack_selection)

        self._import_images.setText("Import Images")
        self._import_images.setShortcut(QKeySequence.StandardKey.Open)
        self._import_images.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._import_images)

        self._flip_selection.setText("Flip Selection")
        self._flip_selection.setShortcut(QKeySequence(Qt.Key.Key_M))
        self._flip_selection.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._flip_selection)

        self._bilinear_filtering.setText("Bilinear Filtering")
        self._bilinear_filtering.setCheckable(True)
        self.addAction(self._bilinear_filtering)

        self._project_new.setText("New Project")
        self._project_new.setShortcut(QKeySequence.StandardKey.New)
        self._project_new.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._project_new)

        self._project_save.setText("Save Project")
        self._project_save.setShortcut(QKeySequence.StandardKey.Save)
        self._project_save.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._project_save)

        self._project_open.setText("Open Project")
        self._project_open.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self._project_open.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._project_open)

        self._reset_view.setText("Reset View")
        self.addAction(self._reset_view)

        self._ignore_mouse.setText("Ignore Mouse")
        self._ignore_mouse.setCheckable(True)
        self.addAction(self._ignore_mouse)

        self._delete_selection.setText("Delete")
        self._delete_selection.setShortcut(QKeySequence.StandardKey.Delete)
        self._delete_selection.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._delete_selection)

        self._quit.setText("Quit")
        self._quit.setShortcut(QKeySequence.StandardKey.Quit)
        self._quit.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self._quit)

        self._export_selection.setText("Export Selection")
        self.addAction(self._export_selection)

        self._always_on_top.setText("Always on Top")
        self._always_on_top.setCheckable(True)
        self.addAction(self._always_on_top)

        self._menu.addAction(self._undo)
        self._menu.addAction(self._redo)

        self._menu.addSeparator()
        self._menu.addAction(self._grayscale)
        self._menu.addAction(self._bilinear_filtering)
        self._menu.addAction(self._ignore_mouse)
        self._menu.addAction(self._always_on_top)

        self._menu.addSeparator()
        self._menu.addAction(self._select_all)
        self._menu.addAction(self._flip_selection)
        self._menu.addAction(self._pack_selection)
        self._menu.addAction(self._delete_selection)

        self._menu.addSeparator()
        self._menu.addAction(self._project_new)
        self._menu.addAction(self._project_save)
        self._menu.addAction(self._project_open)

        self._menu.addSeparator()
        self._menu.addAction(self._import_images)
        self._menu.addAction(self._export_selection)
        self._menu.addAction(self._reset_view)

        self._menu.addSeparator()
        self._menu.addAction(self._quit)
