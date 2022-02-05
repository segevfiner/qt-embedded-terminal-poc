import sys
import pathlib
import threading
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

        self.channel = QtWebChannel.QWebChannel(self)
        self.webview.page().setWebChannel(self.channel)

        self.api = TerminalAPI(self)
        self.channel.registerObject("term", self.api)

        self.webview.load(QtCore.QUrl.fromLocalFile(str(_SCRIPT_DIR / "index.html")))

        self.proc = PtyProcess.spawn(["pwsh"])
        self.read_thread = threading.Thread(target=self.read_thread_main)
        self.read_thread.start()

    def closeEvent(self, event):
        self.proc.close(force=True)
        self.read_thread.join()

    def read_thread_main(self):
        # TODO Something more robust to wait for the API to connect?
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
