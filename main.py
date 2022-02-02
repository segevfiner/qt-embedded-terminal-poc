import sys
import pathlib
from PySide2 import QtCore, QtWidgets, QtWebEngine, QtWebEngineWidgets


_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent


class EmbeddedTerminal(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumWidth(640)
        self.setMinimumHeight(480)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(QtCore.QMargins())

        self.webview = QtWebEngineWidgets.QWebEngineView(self)
        self.webview.load(QtCore.QUrl.fromLocalFile(str(_SCRIPT_DIR / "index.html")))

        layout.addWidget(self.webview)


def main():
    QtWebEngine.QtWebEngine.initialize()

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)

    window = EmbeddedTerminal()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
