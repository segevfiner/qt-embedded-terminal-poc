import sys
import pathlib
import threading
import typing
from winpty import PtyProcess
from PySide2 import QtCore, QtWidgets, QtWebEngine, QtWebEngineWidgets, QtWebChannel, QtNetwork, QtWebSockets


_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent


class TerminalAPI(QtCore.QObject):
    def __init__(self, term=None):
        super().__init__(term)
        self.term = term

    input = QtCore.Signal(str)

    @QtCore.Slot(str)
    def write(self, text: str):
        # print("write:", repr(text))
        self.term.proc.write(text)

    @QtCore.Slot(int, int)
    def resize(self, cols: int, rows: int):
        # print("write:", repr(text))
        self.term.proc.setwinsize(rows, cols)


class WebSocketTransport(QtWebChannel.QWebChannelAbstractTransport):
    def __init__(self, socket: QtWebSockets.QWebSocket):
        super().__init__(socket)
        self.socket = socket

        self.socket.textMessageReceived.connect(self.textMessageReceived)
        self.socket.disconnected.connect(self.deleteLater)

    def sendMessage(self, message: typing.Dict) -> None:
        doc = QtCore.QJsonDocument(message)
        self.socket.sendTextMessage(str(doc.toJson(QtCore.QJsonDocument.Compact), "utf-8"))

    @QtCore.Slot()
    def textMessageReceived(self, messageData: str):
        error = QtCore.QJsonParseError()
        message = QtCore.QJsonDocument.fromJson(messageData.encode(), error)

        if error.error:
            print(f"Failed to parse text message as JSON object: {messageData}, Error is: {error.errorString()}", file=sys.stderr)
            return
        elif not message.isObject():
            print(f"Received JSON message that is not an object: {messageData}", file=sys.stderr)

        self.messageReceived.emit(message.object(), self)


class EmbeddedTerminal(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Qt Embedded Terminal Demo")
        self.setMinimumWidth(640)
        self.setMinimumHeight(480)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(QtCore.QMargins())

        self.webview = QtWebEngineWidgets.QWebEngineView(self)

        layout.addWidget(self.webview)

        self.server = QtWebSockets.QWebSocketServer("qt-embedded-terminal", QtWebSockets.QWebSocketServer.NonSecureMode, self)
        self.server.newConnection.connect(self.handleNewConnection)
        if not self.server.listen(QtNetwork.QHostAddress.LocalHost, 0):
            raise RuntimeError("Failed to start WebSocket server")

        self.channel = QtWebChannel.QWebChannel(self)

        self.api = TerminalAPI(self)
        self.channel.registerObject("term", self.api)

        url = QtCore.QUrl.fromLocalFile(str(_SCRIPT_DIR / "index.html"))
        url.setQuery(f"port={self.server.serverPort()}")
        self.webview.load(url)

        self.proc = PtyProcess.spawn(["pwsh"])
        self.read_thread = threading.Thread(target=self.read_thread_main)

    def closeEvent(self, event):
        self.proc.close(force=True)
        self.read_thread.join()

    def handleNewConnection(self):
        self.channel.connectTo(WebSocketTransport(self.server.nextPendingConnection()))
        self.read_thread.start()

    def read_thread_main(self):
        import time; time.sleep(1)
        try:
            while True:
                data = self.proc.read()
                # print("read:", repr(data))
                self.api.input.emit(data)
        except (EOFError, ConnectionAbortedError):
            pass


def main():
    QtWebEngine.QtWebEngine.initialize()

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)

    window = EmbeddedTerminal()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
