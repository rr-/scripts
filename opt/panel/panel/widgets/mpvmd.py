import json
import math
import os
import socket
import typing as T

from PyQt5 import QtGui, QtWidgets

from panel.widgets.widget import Widget

SOCKET_PATH = "/tmp/mpvmd.socket"


def _format_time(seconds: int) -> str:
    seconds = math.floor(float(seconds))
    return "%02d:%02d" % (seconds // 60, seconds % 60)


class Info:
    def __init__(self) -> None:
        self.raw: T.Dict = {}

    @property
    def path(self) -> T.Optional[str]:
        return self.raw.get("path", None)

    @property
    def pause(self) -> bool:
        return self.raw.get("pause", False)

    @property
    def metadata(self) -> T.Dict:
        return {
            key.lower(): value
            for key, value in (self.raw.get("metadata") or {}).items()
        }

    @property
    def elapsed(self) -> int:
        return self.raw.get("time-pos", 0)

    @property
    def duration(self) -> int:
        return self.raw.get("duration", 0)

    @property
    def random_playback(self) -> bool:
        return (
            self.raw.get("script-opts", {}).get("random_playback", "no")
        ) == "yes"


class Connection:
    def __init__(self) -> None:
        self._request_id = 0
        self._socket: T.Optional[socket.socket] = None
        self.info = Info()

    @property
    def connected(self) -> bool:
        return self._socket is not None

    def connect(self) -> None:
        if self.connected:
            return

        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.settimeout(3)
        self._socket.setblocking(True)

        try:
            self._socket.connect(SOCKET_PATH)
        except ConnectionRefusedError:
            self._socket = None
            raise

        self._request_id = 1

        properties = [
            "pause",
            "time-pos",
            "duration",
            "script-opts",
            "metadata",
            "path",
        ]
        for i, name in enumerate(properties, 1):
            self.send(["observe_property", i, name])

    def send(self, command: T.List[T.Any]) -> None:
        if not self.connected:
            raise RuntimeError("not connected")

        message = {"command": command, "request_id": self._request_id}
        self._send(message)
        self._request_id += 1

    def process(self) -> None:
        if not self.connected:
            return

        for event in self._recv():
            if event.get("event") != "property-change":
                continue
            self.info.raw[event["name"]] = event["data"]

    def _send(self, message: T.Any) -> None:
        print("out", message)
        assert self._socket is not None
        try:
            self._socket.send((json.dumps(message) + "\n").encode())
        except (BrokenPipeError, ValueError):
            self._socket = None
            raise

    def _recv(self) -> T.List[T.Any]:
        assert self._socket is not None
        data = b""
        try:
            while True:
                chunk = self._socket.recv(1024)
                data += chunk
                if chunk.endswith(b"\n") or not chunk:
                    break
        except (BrokenPipeError, ValueError):
            self._socket = None
            raise
        ret = []
        for line in data.decode().split("\n"):
            if line:
                ret.append(json.loads(line))
        print("in", ret)
        return ret


class MpvmdWidget(Widget):
    delay = 0

    def __init__(
        self, app: QtWidgets.QApplication, main_window: QtWidgets.QWidget
    ) -> None:
        super().__init__(app, main_window)
        self._connection = Connection()
        self._info = self._connection.info

        self._container = QtWidgets.QWidget()
        self._status_icon_label = QtWidgets.QLabel(self._container)
        self._song_label = QtWidgets.QLabel(self._container)
        self._shuffle_icon_label = QtWidgets.QLabel(self._container)

        layout = QtWidgets.QHBoxLayout(self._container, margin=0, spacing=6)
        layout.addWidget(self._status_icon_label)
        layout.addWidget(self._song_label)
        layout.addWidget(self._shuffle_icon_label)

        self._status_icon_label.mouseReleaseEvent = self._play_pause_clicked
        self._song_label.mouseReleaseEvent = self._play_pause_clicked
        self._shuffle_icon_label.mouseReleaseEvent = self._shuffle_clicked
        self._status_icon_label.wheelEvent = self._prev_or_next_track
        self._song_label.wheelEvent = self._prev_or_next_track

    @property
    def container(self) -> QtWidgets.QWidget:
        return self._container

    @property
    def available(self) -> bool:
        return os.path.exists(SOCKET_PATH)

    def _play_pause_clicked(self, _event: QtGui.QMouseEvent) -> None:
        with self.exception_guard():
            if self._info.pause:
                self._connection.send(["set_property", "pause", "no"])
            else:
                self._connection.send(["set_property", "pause", "yes"])
            self.refresh()
            self.render()

    def _prev_or_next_track(self, event: QtGui.QWheelEvent) -> None:
        with self.exception_guard():
            self._connection.send(
                [
                    "script-message-to",
                    "playlist",
                    "playlist-next"
                    if event.angleDelta().y() > 0
                    else "playlist-prev",
                ]
            )
            self.refresh()
            self.render()

    def _shuffle_clicked(self, _event: QtGui.QMouseEvent) -> None:
        with self.exception_guard():
            data = self._info.raw["script-opts"].copy()
            data["random_playback"] = (
                "no" if self._info.random_playback else "yes"
            )
            self._connection.send(["set_property", "script-opts", data])

            self.refresh()
            self.render()

    def _refresh_impl(self) -> None:
        try:
            if not self._connection.connected:
                self._connection.connect()
            self._connection.process()
        except (ConnectionRefusedError, BrokenPipeError, ValueError):
            self.delay = min(60, self.delay + 1)
            raise
        else:
            self.delay = 0

    def _render_impl(self) -> None:
        if self._info.pause:
            self._set_icon(self._status_icon_label, "pause")
        else:
            self._set_icon(self._status_icon_label, "play")

        text = ""
        if self._info.metadata.get("title"):
            if self._info.metadata.get("artist"):
                text = (
                    self._info.metadata["artist"]
                    + " - "
                    + self._info.metadata["title"]
                )
            else:
                text = self._info.metadata["title"]
        elif self._info.metadata.get("icy-title"):
            text = self._info.metadata["icy-title"]
        else:
            text = os.path.basename(self._info.path or "")

        if self._info.elapsed and self._info.duration:
            text += " %s / %s" % (
                _format_time(self._info.elapsed),
                _format_time(self._info.duration),
            )

        self._song_label.setText(text)

        shuffle = self._info.random_playback
        if self._shuffle_icon_label.property("active") != shuffle:
            self._shuffle_icon_label.setProperty("active", shuffle)
            if shuffle:
                self._set_icon(self._shuffle_icon_label, "shuffle-on")
            else:
                self._set_icon(self._shuffle_icon_label, "shuffle-off")
