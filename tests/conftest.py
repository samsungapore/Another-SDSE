import sys
import types
from pathlib import Path

# pytest 9's default import mode can avoid putting the project root on sys.path.
# Make sure top-level modules (save.py, po_io.py, etc.) are importable.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DummySignal:
    def __init__(self):
        self._cbs = []

    def connect(self, cb):
        self._cbs.append(cb)

    def emit(self, *a, **kw):
        for cb in list(self._cbs):
            cb(*a, **kw)


class DummyAction:
    def __init__(self):
        self.triggered = DummySignal()


class DummyButton:
    def __init__(self):
        self.clicked = DummySignal()

    def setDisabled(self, v):
        self._disabled = bool(v)


class DummyLabel:
    def __init__(self):
        self._text = ""

    def setText(self, t):
        self._text = t

    def text(self):
        return self._text

    def setPixmap(self, *_):
        pass


class DummyLineEdit:
    def __init__(self):
        self._text = ""
        self.returnPressed = DummySignal()

    def setText(self, t):
        self._text = t

    def text(self):
        return self._text

    def setDisabled(self, v):
        self._disabled = bool(v)


class DummyTextEdit:
    def __init__(self):
        self._text = ""
        self._disabled = False
        self.textChanged = DummySignal()
        self.cursorPositionChanged = DummySignal()

    def setPlainText(self, t):
        self._text = t
        self.textChanged.emit()

    def toPlainText(self):
        return self._text

    def setDisabled(self, v):
        self._disabled = bool(v)

    def setFocus(self):
        pass

    def moveCursor(self, *_):
        pass

    def textCursor(self):
        return DummyCursor(self._text)


class DummyCursor:
    def __init__(self, text: str):
        self._text = text

    def columnNumber(self):
        return 0

    def position(self):
        return 0


class DummyLCD:
    def __init__(self):
        self.value = None

    def display(self, v):
        self.value = v


class DummyProgress:
    def __init__(self):
        self.value = 0

    def setValue(self, v):
        self.value = int(v)


class DummyListItem:
    def __init__(self, text: str):
        self._text = text

    def text(self):
        return self._text


class DummyListWidget:
    def __init__(self):
        self._items = []
        self._cur = -1
        self.currentItemChanged = DummySignal()
        self.currentRowChanged = DummySignal()
        self.itemDoubleClicked = DummySignal()

    def clear(self):
        self._items = []
        self._cur = -1

    def addItems(self, items):
        for it in items:
            self._items.append(DummyListItem(it))

    def addItem(self, it):
        self._items.append(DummyListItem(it))

    def item(self, i):
        return self._items[i]

    def currentRow(self):
        return self._cur

    def count(self):
        return len(self._items)

    def setCurrentItem(self, item):
        prev = self.currentItem()
        self._cur = self._items.index(item)
        self.currentItemChanged.emit(item, prev)

    def setCurrentRow(self, row: int):
        if row < 0 or row >= len(self._items):
            self._cur = -1
            self.currentRowChanged.emit(-1)
            return
        self._cur = row
        self.currentRowChanged.emit(row)

    def sortItems(self):
        self._items.sort(key=lambda it: it.text())

    def currentItem(self):
        if self._cur < 0:
            return None
        return self._items[self._cur]


class DummyTreeWidget:
    def __init__(self):
        self.itemDoubleClicked = DummySignal()
        self._current = None

    def setHeaderItem(self, *_):
        pass

    def addTopLevelItems(self, items):
        self._top = items

    def currentItem(self):
        return self._current

    def setCurrentItem(self, item):
        self._current = item

    def itemAt(self, *_):
        return self._current

    def setFocus(self):
        pass

    def exec_(self):
        return 0

    def collapseItem(self, *_):
        pass

    def expandItem(self, *_):
        pass

    def scrollToItem(self, *_):
        pass


class DummyButtonBox:
    def __init__(self):
        self.accepted = DummySignal()
        self.rejected = DummySignal()


class DummyDialog:
    def __init__(self):
        self.treeWidget = DummyTreeWidget()
        self.open_btn_box = DummyButtonBox()

    def show(self):
        pass

    def setFocus(self):
        pass

    def exec_(self):
        return 0

    def close(self):
        pass


class DummyMessageBox:
    Save = 1
    Discard = 2
    Cancel = 3
    Ok = 0

    @staticmethod
    def warning(*_a, **_kw):
        return DummyMessageBox.Ok

    @staticmethod
    def information(*_a, **_kw):
        return DummyMessageBox.Ok

    @staticmethod
    def question(*_a, **_kw):
        # default: Discard
        return DummyMessageBox.Discard


def _install_qt_stubs():
    # PyQt5 stubs
    pyqt5 = types.ModuleType("PyQt5")
    qtcore = types.ModuleType("PyQt5.QtCore")
    qtgui = types.ModuleType("PyQt5.QtGui")
    qtwidgets = types.ModuleType("PyQt5.QtWidgets")

    class QThread:
        def __init__(self):
            pass

        def wait(self):
            return

        def start(self):
            # Synchronous start for tests.
            if hasattr(self, 'run'):
                self.run()

    def pyqtSignal(*_a, **_kw):
        return DummySignal()

    qtcore.QThread = QThread
    qtcore.pyqtSignal = pyqtSignal
    qtcore.Qt = types.SimpleNamespace()

    class QPixmap:
        def __init__(self, *_a, **_kw):
            pass

    qtgui.QPixmap = QPixmap

    class QIcon:
        def __init__(self, *_):
            pass

    qtgui.QIcon = QIcon
    class QKeySequence:
        Find = object()
        Open = object()
        Save = object()
        Print = object()
        MoveToPreviousPage = object()
        MoveToNextPage = object()

        def __init__(self, *_a, **_kw):
            pass

    qtgui.QKeySequence = QKeySequence

    class QTextCursor:
        EndOfLine = 0

    qtgui.QTextCursor = QTextCursor

    class QApplication:
        def __init__(self, *_):
            pass

        def exec_(self):
            return 0

    class QMainWindow:
        def __init__(self, *_):
            pass

        def setWindowIcon(self, *_):
            pass

        def setWindowTitle(self, *_):
            self._title = _[0] if _ else ""

        def show(self):
            pass

        def setFocus(self):
            pass

    qtwidgets.QApplication = QApplication
    qtwidgets.QMainWindow = QMainWindow
    qtwidgets.QDialog = DummyDialog

    class QTreeWidgetItem:
        def __init__(self, parent=None, *_a, **_kw):
            self._text = {}
            self._expanded = False
            self._parent = parent

        def setText(self, col, text):
            self._text[col] = text

        def text(self, col):
            return self._text.get(col, "")

        def parent(self):
            return self._parent

        def isExpanded(self):
            return self._expanded

    qtwidgets.QTreeWidgetItem = QTreeWidgetItem
    qtwidgets.QMessageBox = DummyMessageBox

    class QShortcut:
        def __init__(self, *_a, **_kw):
            self.activated = DummySignal()

    qtwidgets.QShortcut = QShortcut

    pyqt5.QtCore = qtcore
    pyqt5.QtGui = qtgui
    pyqt5.QtWidgets = qtwidgets

    sys.modules.setdefault("PyQt5", pyqt5)
    sys.modules.setdefault("PyQt5.QtCore", qtcore)
    sys.modules.setdefault("PyQt5.QtGui", qtgui)
    sys.modules.setdefault("PyQt5.QtWidgets", qtwidgets)

    # qtpy.uic stub
    qtpy = types.ModuleType("qtpy")
    uic = types.ModuleType("qtpy.uic")

    def loadUi(_path, obj):
        # Attach minimal widgets/actions expected by editor_ui.
        # Main window + dialogs share a bunch of attributes in this stub.
        obj.open_file = getattr(obj, 'open_file', DummyAction())
        obj.open_f_toolbox = getattr(obj, 'open_f_toolbox', DummyButton())
        obj.save_action = getattr(obj, 'save_action', DummyAction())
        obj.save_toolbox = getattr(obj, 'save_toolbox', DummyButton())
        obj.delete_json_file = getattr(obj, 'delete_json_file', DummyAction())

        obj.txt_files = getattr(obj, 'txt_files', DummyListWidget())

        obj.translated = getattr(obj, 'translated', DummyTextEdit())
        obj.comment = getattr(obj, 'comment', DummyTextEdit())
        obj.original = getattr(obj, 'original', DummyTextEdit())
        obj.japanese = getattr(obj, 'japanese', DummyTextEdit())

        obj.speaker = getattr(obj, 'speaker', DummyLabel())
        obj.jp_text = getattr(obj, 'jp_text', DummyLineEdit())
        obj.jp_result = getattr(obj, 'jp_result', DummyTextEdit())
        obj.search_btn = getattr(obj, 'search_btn', DummyButton())

        obj.prev_script = getattr(obj, 'prev_script', DummyButton())
        obj.next_script = getattr(obj, 'next_script', DummyButton())

        obj.copy_from_original = getattr(obj, 'copy_from_original', DummyButton())
        obj.copy_from_japanese = getattr(obj, 'copy_from_japanese', DummyButton())
        obj.reload = getattr(obj, 'reload', DummyButton())
        obj.search_in_data = getattr(obj, 'search_in_data', DummyButton())

        obj.script_name = getattr(obj, 'script_name', DummyLabel())
        obj.progress_file_label = getattr(obj, 'progress_file_label', DummyLabel())
        obj.global_progress_label = getattr(obj, 'global_progress_label', DummyLabel())
        obj.overall_progress_label = getattr(obj, 'overall_progress_label', DummyLabel())

        obj.xml_progress = getattr(obj, 'xml_progress', DummyProgress())
        obj.overall_progress = getattr(obj, 'overall_progress', DummyProgress())

        obj.line_count = getattr(obj, 'line_count', DummyLCD())
        obj.check_line_icon = getattr(obj, 'check_line_icon', DummyLabel())

        # Search dialog widgets
        obj.search_le = getattr(obj, 'search_le', DummyLineEdit())
        obj.file_list = getattr(obj, 'file_list', DummyListWidget())

        # open/search dialogs
        if isinstance(obj, DummyDialog):
            obj.treeWidget = getattr(obj, 'treeWidget', DummyTreeWidget())
            obj.open_btn_box = getattr(obj, 'open_btn_box', DummyButtonBox())

    uic.loadUi = loadUi
    qtpy.uic = uic

    sys.modules.setdefault("qtpy", qtpy)
    sys.modules.setdefault("qtpy.uic", uic)


_install_qt_stubs()
