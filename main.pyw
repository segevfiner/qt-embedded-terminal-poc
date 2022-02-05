from os import environ
import sys
import pathlib
import threading
import argparse
import struct
if sys.platform == "win32":
    from winpty import PtyProcess
else:
    import termios
    import pty
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
        if sys.platform == "win32":
            self.term.proc.write(text)
        else:
            os.write(self.term.pty, text.encode())

    @QtCore.Slot(int, int)
    def resize(self, cols: int, rows: int):
        # print("write:", repr(text))
        if sys.platform == "win32":
            self.term.proc.setwinsize(rows, cols)
        else:
            s = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.term.pty, termios.TIOCSWINSZ, s)


class EmbeddedTerminal(QtWidgets.QWidget):
    def __init__(self, shell, parent=None):
        super().__init__(parent=parent)

        self.shell = shell

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

        if sys.platform == "win32":
            self.proc = PtyProcess.spawn([self.shell])
        else:
            self.pid, self.pty = pty.fork()
            if self.pid == 0:
                os.execlp(self.shell, self.shell)

        self.read_thread = threading.Thread(target=self.read_thread_main)
        self.read_thread.start()

    def closeEvent(self, event):
        if sys.platform == "win32":
            self.proc.close(force=True)
        else:
            os.close(self.pty)
            os.waitpid(self.pid, 0)

        self.read_thread.join()

    def read_thread_main(self):
        # TODO Something more robust to wait for the API to connect?
        import time; time.sleep(1)
        try:
            while True:
                if sys.platform == "win32":
                    data = self.proc.read()
                else:
                    data = os.read(self.pty, 1024).decode()
                # print("read:", repr(data))
                self.api.input.emit(data)
        except (EOFError, ConnectionAbortedError):
            pass


def main():
    QtWebEngine.QtWebEngine.initialize()

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument("--shell", default="pwsh" if sys.platform == "win32" else os.environ["SHELL"])
    # TODO Create a login shell by default on Linux (But not on macOS)

    args = parser.parse_args()

    window = EmbeddedTerminal(shell=args.shell)
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
