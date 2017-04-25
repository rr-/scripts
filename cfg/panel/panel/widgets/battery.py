import glob
import time
from PyQt5 import QtWidgets
from panel.widgets.widget import Widget


def read_file(path):
    with open(path, 'r') as handle:
        return handle.read().strip()


class BatteryWidget(Widget):
    delay = 3

    def __init__(self, app, main_window):
        super().__init__(app, main_window)
        self.percentage = None
        try:
            self._charge_now = glob.glob(
                '/sys/class/power_supply/*/energy_now')[0]
            self._charge_max = glob.glob(
                '/sys/class/power_supply/*/energy_full')[0]
            self._label = QtWidgets.QLabel()
            main_window[0].layout().addWidget(self._label)
            self.battery_present = True
        except IndexError:
            self.battery_present = False

    def refresh_impl(self):
        if self.battery_present:
            current_value = int(read_file(self._charge_now))
            max_value = int(read_file(self._charge_max))
            self.percentage = current_value * 100.0 / max_value
            time.sleep(3)

    def render_impl(self):
        if self.battery_present:
            self._label.setText('Battery: %5.02f%%' % self.percentage)