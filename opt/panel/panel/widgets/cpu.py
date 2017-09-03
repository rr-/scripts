import psutil
from PyQt5 import QtCore, QtWidgets
from panel.widgets.chart import Chart
from panel.widgets.widget import Widget
from panel.colors import Colors


class CpuWidget(Widget):
    delay = 0

    def __init__(self, app, main_window):
        super().__init__(app, main_window)
        self.percentage = None
        self._container = QtWidgets.QWidget(main_window)
        self._icon_label = QtWidgets.QLabel(self._container)
        self._text_label = QtWidgets.QLabel(self._container)
        self._chart = Chart(self._container, 80)

        layout = QtWidgets.QHBoxLayout(self._container, margin=0, spacing=6)
        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)
        layout.addWidget(self._chart)

        self._text_label.setFixedWidth(45)
        self._text_label.setAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self._set_icon(self._icon_label, 'chip')

    @property
    def container(self):
        return self._container

    def _refresh_impl(self):
        if self.percentage is None:
            self.percentage = psutil.cpu_percent(interval=0.1)
        else:
            self.percentage = psutil.cpu_percent(interval=1)

    def _render_impl(self):
        self._text_label.setText('{:.1f}%'.format(self.percentage))
        self._chart.addPoint(Colors.cpu_chart_line, self.percentage)
        self._chart.repaint()
