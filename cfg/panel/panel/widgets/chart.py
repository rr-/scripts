# pylint: disable=invalid-name
import collections
from PyQt5 import QtCore, QtGui, QtWidgets
from panel.colors import Colors


class Chart(QtWidgets.QWidget):
    def __init__(self, min_width):
        super().__init__()
        self.setMinimumSize(QtCore.QSize(min_width, 0))
        self.points = collections.defaultdict(list)
        self.setProperty('class', 'chart')

    def addPoint(self, color, y):
        self.points[color].append(y)

    def paintEvent(self, _event):
        width = self.width()
        height = self.height()

        highest = max(p for points in self.points.values() for p in points)

        def x_transform(x):
            return width - 1 - 2 * x

        def y_transform(y):
            return height - 1 - y * (height - 1) / max(1, highest)

        painter = QtGui.QPainter()
        painter.begin(self)

        painter.setBrush(QtGui.QBrush(QtGui.QColor(Colors.chart_background)))
        painter.setPen(QtGui.QPen(0))
        painter.drawRect(0, 0, width - 1, height - 1)
        painter.setBrush(QtGui.QBrush())

        for color, points in self.points.items():
            painter.setPen(QtGui.QColor(color))
            prev_x = 0
            prev_y = points[-1]
            for x, y in enumerate(reversed(points)):
                dx = x_transform(x)
                excess = dx < 0
                if excess:
                    dx = 0
                painter.drawLine(
                    x_transform(prev_x),
                    y_transform(prev_y),
                    dx,
                    y_transform(y))
                prev_x = x
                prev_y = y
                if excess:
                    points.pop(0)
                    break

        painter.end()
