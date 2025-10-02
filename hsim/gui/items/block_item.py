"""
Graphics items for DES blocks
"""

from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsItemGroup, QMenu, QInputDialog
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter

from hsim.gui.models.block_definitions import get_block_definition, BlockType
from hsim.gui.models.model import Block, Position, Size


class BlockItemSignals(QObject):
    """Signals for BlockItem (QGraphicsItem can't have signals directly)"""
    position_changed = pyqtSignal(str, float, float)  # block_id, x, y
    double_clicked = pyqtSignal(str)  # block_id
    properties_requested = pyqtSignal(object)  # block data
    deleted = pyqtSignal(str)  # block_id


class BlockItem(QGraphicsItemGroup):
    """Visual representation of a DES block"""

    def __init__(self, block: Block, parent=None):
        super().__init__(parent)
        self.block = block
        self.block_def = get_block_definition(BlockType(block.type))
        self.signals = BlockItemSignals()

        # Graphics elements
        self.shape_item = None
        self.text_item = None
        self.icon_item = None

        # State
        self.is_selected = False

        # Setup
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        self.create_graphics()
        self.update_appearance()

    def create_graphics(self):
        """Create the graphical elements"""
        # Create shape based on block definition
        if self.block_def.shape == "circle":
            self.shape_item = QGraphicsEllipseItem(
                0, 0,
                self.block.size.width,
                self.block.size.height
            )
        elif self.block_def.shape == "rounded":
            # For rounded rectangles, we'll use a rectangle with rounded corners
            self.shape_item = QGraphicsRectItem(
                0, 0,
                self.block.size.width,
                self.block.size.height
            )
        else:  # rectangle
            self.shape_item = QGraphicsRectItem(
                0, 0,
                self.block.size.width,
                self.block.size.height
            )

        self.addToGroup(self.shape_item)

        # Add icon text
        self.icon_item = QGraphicsTextItem(self.block_def.icon)
        font = QFont()
        font.setPointSize(24)
        self.icon_item.setFont(font)
        self.icon_item.setDefaultTextColor(QColor("white"))

        # Center icon
        icon_rect = self.icon_item.boundingRect()
        self.icon_item.setPos(
            (self.block.size.width - icon_rect.width()) / 2,
            (self.block.size.height - icon_rect.height()) / 2 - 15
        )
        self.addToGroup(self.icon_item)

        # Add name text
        self.text_item = QGraphicsTextItem(self.block.name)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor("white"))

        # Center text
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            (self.block.size.width - text_rect.width()) / 2,
            self.block.size.height / 2 + 10
        )
        self.addToGroup(self.text_item)

        # Set position
        self.setPos(self.block.position.x, self.block.position.y)

    def update_appearance(self, selected=False):
        """Update the visual appearance"""
        color = QColor(self.block_def.color)
        pen = QPen(QColor("white") if selected else color.darker(120), 3 if selected else 2)
        brush = QBrush(color)

        self.shape_item.setPen(pen)
        self.shape_item.setBrush(brush)

        self.is_selected = selected

    def update_name(self, name):
        """Update the block name"""
        self.block.name = name
        self.text_item.setPlainText(name)

        # Re-center text
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            (self.block.size.width - text_rect.width()) / 2,
            self.block.size.height / 2 + 10
        )

    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            pos = self.pos()
            self.block.position.x = pos.x()
            self.block.position.y = pos.y()
            self.signals.position_changed.emit(self.block.id, pos.x(), pos.y())

        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_appearance(selected=self.isSelected())

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click"""
        if self.block_def.has_fsm:
            self.signals.double_clicked.emit(self.block.id)
        else:
            # Show rename dialog
            from PyQt6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(
                None, "Rename Block",
                "Enter new name:",
                text=self.block.name
            )
            if ok and name:
                self.update_name(name)

    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = QMenu()

        # Rename action
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(self.show_rename_dialog)

        # Properties action
        properties_action = menu.addAction("Properties")
        properties_action.triggered.connect(self.show_properties)

        menu.addSeparator()

        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_block)

        menu.exec(event.screenPos())

    def show_rename_dialog(self):
        """Show rename dialog"""
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            None, "Rename Block",
            "Enter new name:",
            text=self.block.name
        )
        if ok and name:
            self.update_name(name)

    def show_properties(self):
        """Show properties dialog"""
        self.signals.properties_requested.emit(self.block)

    def delete_block(self):
        """Delete this block"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            None, "Delete Block",
            f"Delete block '{self.block.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.signals.deleted.emit(self.block.id)

    def get_center_pos(self):
        """Get the center position of the block"""
        return QPointF(
            self.block.position.x + self.block.size.width / 2,
            self.block.position.y + self.block.size.height / 2
        )

    def get_connection_point(self, angle):
        """Get a point on the edge of the block for connections"""
        # For simplicity, return center for now
        # TODO: Calculate actual edge points based on shape and angle
        return self.get_center_pos()
