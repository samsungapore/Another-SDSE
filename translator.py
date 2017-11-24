# -*- coding: utf-8 -*-

from PyQt5.QtCore import QThread, pyqtSignal

from scrape import get_translation


class SearchThread(QThread):
    parse_triggered = pyqtSignal()
    done = pyqtSignal(list)

    def __init__(self):
        QThread.__init__(self)
        self.jp_text = None

    def __del__(self):
        self.wait()

    def set_jp_text(self, jp_text):
        self.jp_text = jp_text

    def run(self):
        data = get_translation(self.jp_text)
        self.done.emit(data)
