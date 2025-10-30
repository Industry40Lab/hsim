"""
Modern stylesheet for the GUI application
AnyLogic-inspired color scheme and styling
"""

MODERN_STYLESHEET = """
/* Main Window */
QMainWindow {
    background-color: #2b2b2b;
}

/* Menu Bar */
QMenuBar {
    background-color: #3c3c3c;
    color: #ffffff;
    border-bottom: 1px solid #555555;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 12px;
    border-radius: 3px;
}

QMenuBar::item:selected {
    background-color: #4a4a4a;
}

QMenuBar::item:pressed {
    background-color: #0078d4;
}

/* Menus */
QMenu {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 4px;
}

QMenu::item {
    padding: 6px 30px 6px 20px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #0078d4;
}

QMenu::separator {
    height: 1px;
    background-color: #555555;
    margin: 4px 0px;
}

/* Toolbar */
QToolBar {
    background-color: #3c3c3c;
    border: none;
    border-bottom: 1px solid #555555;
    spacing: 3px;
    padding: 4px;
}

QToolBar::separator {
    background-color: #555555;
    width: 1px;
    margin: 4px 6px;
}

QToolButton {
    background-color: transparent;
    color: #ffffff;
    border: none;
    border-radius: 3px;
    padding: 5px;
    margin: 1px;
}

QToolButton:hover {
    background-color: #4a4a4a;
}

QToolButton:pressed {
    background-color: #0078d4;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    border-bottom: none;
    padding: 6px 12px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #2b2b2b;
    border-bottom: 1px solid #2b2b2b;
}

QTabBar::tab:!selected {
    margin-top: 2px;
}

QTabBar::tab:hover:!selected {
    background-color: #4a4a4a;
}

/* Tree Widget */
QTreeWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    border: 1px solid #555555;
    selection-background-color: #0078d4;
    outline: none;
}

QTreeWidget::item {
    padding: 4px;
}

QTreeWidget::item:selected {
    background-color: #0078d4;
}

QTreeWidget::item:hover {
    background-color: #3a3a3a;
}

/* Splitter */
QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #0078d4;
}

/* Status Bar */
QStatusBar {
    background-color: #3c3c3c;
    color: #ffffff;
    border-top: 1px solid #555555;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 12px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Text Edit */
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #555555;
    selection-background-color: #264f78;
}

/* Line Edit */
QLineEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px;
    selection-background-color: #264f78;
}

QLineEdit:focus {
    border: 1px solid #0078d4;
}

/* Buttons */
QPushButton {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border: 1px solid #0078d4;
}

QPushButton:pressed {
    background-color: #0078d4;
}

QPushButton:disabled {
    color: #888888;
    background-color: #2b2b2b;
}

/* Labels */
QLabel {
    color: #ffffff;
}

/* Group Box */
QGroupBox {
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    margin-top: 12px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    color: #0078d4;
}

/* Graphics View (Canvas) */
QGraphicsView {
    background-color: #252525;
    border: 1px solid #555555;
}

/* Dialog */
QDialog {
    background-color: #2b2b2b;
    color: #ffffff;
}

/* Tool Tip */
QToolTip {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 4px;
    border-radius: 3px;
}
"""


def apply_modern_style(app):
    """Apply modern stylesheet to the application"""
    app.setStyleSheet(MODERN_STYLESHEET)
