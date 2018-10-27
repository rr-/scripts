# pylint: disable=invalid-name
import typing as T

from PyQt5 import QtCore, QtGui, QtWidgets

from panel.colors import Colors
from panel.util import run
from panel.widgets.widget import Widget

try:
    import alsaaudio
except ImportError:
    alsaaudio = None


class VolumeControl(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, size: QtCore.QSize) -> None:
        super().__init__(parent)
        self.setMinimumSize(size)
        self.value = 0
        self.max = 100

    def set(self, value: int) -> None:
        self.value = value

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        width = self.width()
        height = self.height()
        margin_x = 3
        margin_y = 3
        inner_width = width - margin_x
        inner_height = height - 1 - 2 * margin_y

        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        points = {
            "zero": QtCore.QPoint(margin_x, height - 1 - margin_y),
            "vol1": QtCore.QPoint(
                margin_x + self.value * inner_width / self.max,
                height - 1 - margin_y,
            ),
            "vol2": QtCore.QPoint(
                margin_x + self.value * inner_width / self.max,
                height - 1 - margin_y - self.value * inner_height / self.max,
            ),
            "max1": QtCore.QPoint(width - 1, margin_y),
            "max2": QtCore.QPoint(width - 1, height - 1 - margin_y),
        }

        poly = [points["zero"], points["vol1"], points["vol2"]]
        painter.setPen(QtGui.QPen(0))
        painter.setBrush(QtGui.QColor(Colors.volume_chart_background))
        painter.drawPolygon(QtGui.QPolygon(poly))

        poly = [points["vol1"], points["vol2"], points["max1"], points["max2"]]
        painter.setBrush(QtGui.QColor(Colors.chart_background))
        painter.drawPolygon(QtGui.QPolygon(poly))

        painter.setPen(QtGui.QPen(QtGui.QColor(Colors.chart_foreground)))
        poly = [points["zero"], points["max1"], points["max2"]]
        painter.setBrush(QtGui.QBrush())
        painter.drawPolygon(QtGui.QPolygon(poly))

        painter.end()


class VolumeWidget(Widget):
    delay = 1

    def __init__(
        self, app: QtWidgets.QApplication, main_window: QtWidgets.QWidget
    ) -> None:
        super().__init__(app, main_window)

        self.volume = 0

        self._container = QtWidgets.QWidget(main_window)
        self._container.mouseReleaseEvent = self.toggle_mute
        self._container.wheelEvent = self.change_volume
        self._icon_label = QtWidgets.QLabel(self._container)
        self._volume_control = VolumeControl(
            self._container, QtCore.QSize(50, 10)
        )

        layout = QtWidgets.QHBoxLayout(self._container, margin=0, spacing=6)
        layout.addWidget(self._icon_label)
        layout.addWidget(self._volume_control)

    @property
    def available(self) -> bool:
        return self.mixer is not None

    @property
    def container(self) -> QtWidgets.QWidget:
        return self._container

    @property
    def mixer(self) -> T.Optional["alsaaudio.Mixer"]:
        if not alsaaudio:
            return None
        return alsaaudio.Mixer(device="pulse")

    def change_volume(self, event: QtGui.QWheelEvent) -> None:
        with self.exception_guard():
            run(
                [
                    "amixer",
                    "-D",
                    "pulse",
                    "set",
                    "Master",
                    "1%" + ["-", "+"][event.angleDelta().y() > 0],
                    "unmute",
                ]
            )
            self.refresh()
            self.render()

    def toggle_mute(self, _event: QtGui.QMouseEvent) -> None:
        if not self.mixer:
            return
        with self.exception_guard():
            self.mixer.setmute(1 - self.mixer.getmute()[0])
            self.refresh()
            self.render()

    def _refresh_impl(self) -> None:
        if not self.mixer:
            return
        self.volume = self.mixer.getvolume()[0]

    def _render_impl(self) -> None:
        if not self.mixer:
            return
        self._set_icon(
            self._icon_label,
            "volume-off" if self.mixer.getmute()[0] else "volume-on",
        )
        self._volume_control.set(self.volume)
        self._volume_control.repaint()
