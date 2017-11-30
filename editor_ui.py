# -*- coding: utf-8 -*-

from os.path import join
from sys import argv, exit, stdout

from PyQt5.QtGui import QPixmap, QIcon, QKeySequence, QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, \
    QTreeWidgetItem, QMessageBox, QShortcut
from os import listdir
from qtpy import uic

from save import get_key
from script_analyser import XmlAnalyser, length_is_okay, cleaned_text, \
    find_w_line, find_to_remove
from translator import SearchThread


class Ui_MainWindow(QMainWindow):
    """
    Another SDSE for your pleasure.
    """

    def __init__(self):
        """
        Initialization of the main GUI
        """
        QMainWindow.__init__(self)
        uic.loadUi('gui/AnotherSDSE.ui', self)

        self.setWindowIcon(QIcon('img/cropped-avatarmiraiteam.ico'))

        self.data = dict()
        self.dupes = dict()

        self.file_has_changed = False

        self.previous_script_name = ''
        self.previous_game = ''
        self.current_game = ''

        self.discard = False

        self.parts = ('Prologue', 'Chapitre 1', 'Chapitre 2', 'Chapitre 3',
                      'Chapitre 4', 'Chapitre 5', 'Chapitre 6', 'Epilogue',
                      'Autres')

        self.games = list()

        self.plaintexts = {
            'TRANSLATED': self.translated,
            'COMMENT': self.comment
        }

        self.worker = SearchThread()

        self.open_ui = QDialog()
        uic.loadUi('gui/open_dialog.ui', self.open_ui)

        self.load_data()
        self.init_open_ui_tree_view()
        self.set_signals()
        self.set_shortcuts()

    def set_signals(self):
        """
        Setting all signals connection between widgets and which
        function they trigger.
        """

        # OPEN FILE
        self.open_file.triggered.connect(self.open_ui_launch)
        self.open_f_toolbox.clicked.connect(self.open_ui_launch)

        # SAVE FILE
        self.save_action.triggered.connect(self.save)
        self.save_toolbox.clicked.connect(self.save)

        self.txt_files.currentItemChanged.connect(self.change_text)

        ######################## OPEN GUI PART ########################

        # TREE VIEW ITEM DOUBLE CLICKED
        self.open_ui.treeWidget.itemDoubleClicked.connect(self.change_file)

        self.open_ui.open_btn_box.accepted.connect(
            lambda: self.change_file(
                item=self.open_ui.treeWidget.currentItem(),
                column=0
            )
        )
        self.open_ui.open_btn_box.rejected.connect(self.close_open_ui)

        ################################################################

        # NAVIGATION BETWEEN SCRIPTS
        self.prev_script.clicked.connect(self.go_prev_script)
        self.next_script.clicked.connect(self.go_next_script)

        self.translated.textChanged.connect(self.check_line_len)
        self.translated.cursorPositionChanged.connect(self.update_line_len)

        self.copy_from_original.clicked.connect(self.copy_from_original_func)
        self.copy_from_japanese.clicked.connect(self.copy_from_japanese_func)

        # TRANSLATOR JISHO
        self.jp_text.returnPressed.connect(self.jisho_search)
        self.search_btn.clicked.connect(self.jisho_search)
        
        # RELOAD BUTTON
        self.reload.clicked.connect(self.reload_ui)

    def set_shortcuts(self):
        open_sc = QShortcut(QKeySequence(QKeySequence.Open), self)
        save_sc = QShortcut(QKeySequence(QKeySequence.Save), self)
        copy_from_original_sc = QShortcut(QKeySequence(QKeySequence.Print), self)
        go_prev_script_sc = QShortcut(QKeySequence(QKeySequence.MoveToPreviousPage), self)
        go_next_script_sc = QShortcut(QKeySequence(QKeySequence.MoveToNextPage), self)

        open_sc.activated.connect(self.open_ui_launch)
        save_sc.activated.connect(self.save)
        copy_from_original_sc.activated.connect(self.copy_from_original_func)
        go_prev_script_sc.activated.connect(self.go_prev_script)
        go_next_script_sc.activated.connect(self.go_next_script)

    def load_data(self):
        """
        Loads the data present in /script_data
        """

        if len(listdir('./script_data/')) == 0:
            return
        percent = 100 / (len(listdir('./script_data/')) * 6)
        total = percent
        to_retrieve = ('TRANSLATED', 'ORIGINAL', 'JAPANESE', 'COMMENT',
                       'SPEAKER')

        for game in listdir('./script_data/'):
            stdout.write('\r' + str(round(total, 2)) + ' %')
            total += percent
            self.data[game] = XmlAnalyser("./script_data/" + game)
            
            for tagname in to_retrieve:
                stdout.write('\r' + str(round(total, 2)) + ' %')
                total += percent
                self.data[game].analyse_scripts(tagname)
            print('\r' + game + ' loaded.')
            self.games.append(game)

    def check_files_modifications(self):
        ret = self.modification_has_been_made('TRANSLATED')

        if ret == 1:
            self.save()
        elif ret == 2:
            return
        elif ret == 0:
            self.discard = True
        else:
            ret = self.modification_has_been_made('COMMENT')

            if ret == 1:
                self.save()
            elif ret == 2:
                return
            elif ret == 0:
                self.discard = True

    def reload_ui(self, update_curr_text=True):
        """
        Reload data from XML
        """

        if self.current_game != '':

            self.check_files_modifications()

            self.data[self.current_game] = XmlAnalyser("./script_data/" + self.current_game)
            self.data[self.current_game].analyse_scripts('TRANSLATED')
            self.data[self.current_game].analyse_scripts('ORIGINAL')
            self.data[self.current_game].analyse_scripts('JAPANESE')
            self.data[self.current_game].analyse_scripts('COMMENT')
            self.data[self.current_game].analyse_scripts('SPEAKER')
            if update_curr_text:
                self.change_text(self.txt_files.currentItem(), None)

    def init_open_ui_tree_view(self):
        """
        Initialize the tree widget of the "open gui" according to
        the data loaded
        """

        main_treew_item = QTreeWidgetItem()
        main_treew_item.setText(0, 'Script')
        self.open_ui.treeWidget.setHeaderItem(main_treew_item)

        main_tree_w = list()

        for game in self.games:
            qtreewidgetitem = QTreeWidgetItem()
            qtreewidgetitem.setText(0, game)
            main_tree_w.append(qtreewidgetitem)

            tree_widgets = list()
            for part in self.parts:
                treewidgetitem = QTreeWidgetItem(qtreewidgetitem)
                treewidgetitem.setText(0, part)
                tree_widgets.append(treewidgetitem)

            for elem in sorted(list(self.data[game].script_data['ORIGINAL'].keys())):
                if elem[1:3].isnumeric() and int(elem[1:3]) <= 7:
                    childtree = QTreeWidgetItem(tree_widgets[int(elem[2])])
                else:
                    childtree = QTreeWidgetItem(tree_widgets[-1])
                childtree.setText(0, elem)

        self.open_ui.treeWidget.addTopLevelItems(main_tree_w)

    def open_ui_launch(self):
        """
        Method to launch the "open gui"
        """
        self.open_ui.show()
        self.open_ui.setFocus()
        if self.open_ui.treeWidget.currentItem() is None:
            self.open_ui.treeWidget.setCurrentItem(self.open_ui.treeWidget.itemAt(0, 0))
        self.open_ui.treeWidget.setFocus()
        self.open_ui.exec_()

    def close_open_ui(self):
        """
        this method closes the "open gui"
        """
        self.open_ui.close()
        self.setFocus()

    def change_file(self, item, column):
        if item.text(column) not in self.parts and item.text(column) not in self.games:
            self.close_open_ui()

            if self.current_game != '':
                self.check_files_modifications()

            script_name = item.text(column)
            if not self.script_name.text() == '':
                self.previous_script_name = self.script_name.text()
            else:
                self.previous_script_name = script_name

            self.script_name.setText(script_name)
            self.setWindowTitle(script_name + ' - Another SDSE 1.0')

            if not self.current_game == '':
                self.previous_game = self.current_game
            else:
                self.previous_game = item.parent().parent().text(0)
            self.current_game = item.parent().parent().text(0)
            self.overall_progress_label.setText('Progression Totale sur ' + self.current_game)
            # set the script files in the window
            txt_files = self.data[self.current_game].script_data['ORIGINAL'][script_name]
            list_of_txt_index = [str(i) for i in range(len(txt_files))]
            self.file_has_changed = True
            self.txt_files.clear()
            self.txt_files.addItems(list_of_txt_index)
            self.txt_files.setCurrentItem(self.txt_files.item(0))
            self.reload_ui()
        else:
            if item.isExpanded():
                self.open_ui.treeWidget.collapseItem(item)
            else:
                self.open_ui.treeWidget.expandItem(item)

            self.open_ui.treeWidget.scrollToItem(item)

    def change_text(self, item, previous_item):
        if item is None:
            item = self.txt_files.item(0)
        script_index = item.text()

        # update data if previous item exists
        if previous_item is not None:
            prev_script_index = previous_item.text()
            if self.file_has_changed:
                if not self.discard:
                    self.data[self.previous_game].script_data['TRANSLATED'][self.previous_script_name][int(prev_script_index)] = '\n' + self.translated.toPlainText().strip('\n').strip() + '\n'
                    self.data[self.previous_game].script_data['COMMENT'][self.previous_script_name][int(prev_script_index)] = '\n' + self.comment.toPlainText().strip('\n').strip() + '\n'
                else:
                    self.discard = False
                self.file_has_changed = False
            else:
                if not self.discard:
                    self.data[self.current_game].script_data['TRANSLATED'][self.script_name.text()][int(prev_script_index)] = '\n' + self.translated.toPlainText().strip('\n').strip() + '\n'
                    self.data[self.current_game].script_data['COMMENT'][self.script_name.text()][int(prev_script_index)] = '\n' + self.comment.toPlainText().strip('\n').strip() + '\n'
                else:
                    self.discard = False

        translated_text = self.data[self.current_game].script_data['TRANSLATED'][self.script_name.text()][int(script_index)][1:-1]
        original_text = self.data[self.current_game].script_data['ORIGINAL'][self.script_name.text()][int(script_index)][1:-1]
        comment_text = self.data[self.current_game].script_data['COMMENT'][self.script_name.text()][int(script_index)][1:-1]
        speaker = self.data[self.current_game].script_data['SPEAKER'][self.script_name.text()][int(script_index)]
        if speaker == 'NO NAME':
            speaker = 'Narrateur'
        else:
            speaker = speaker.lower().split(' ')
            tmp = str()
            for word in speaker:
                tmp += word.capitalize() + ' '
            speaker = tmp[:-1]
        try:
            japanese_text = self.data[self.current_game].script_data['JAPANESE'][self.script_name.text()][int(script_index)][1:-1]
        except IndexError:
            japanese_text = ''

        self.translated.setPlainText(translated_text)
        self.original.setPlainText(original_text)
        self.comment.setPlainText(comment_text)
        self.japanese.setPlainText(japanese_text)
        self.speaker.setText("Locuteur : %s" % speaker)

        if self.japanese.toPlainText() != '':
            self.jp_text.setText(cleaned_text(self.japanese.toPlainText()))

        cursor = self.translated.textCursor()
        self.line_count.display(cursor.columnNumber())

        # activate navigation tool boxes
        self.prev_script.setDisabled(False)
        self.next_script.setDisabled(False)

        # activate editing
        self.translated.setDisabled(False)
        self.comment.setDisabled(False)

        # set_focus
        self.translated.setFocus()
        self.translated.moveCursor(QTextCursor.EndOfLine)

        # compute file progress
        self.compute_file_progress()
        self.compute_global_progress()

    def compute_file_progress(self):
        translated_count = 0
        total_txt = len(self.data[self.current_game].script_data['TRANSLATED'][
                            self.script_name.text()])
        for k in range(total_txt):
            if self.data[self.current_game].script_data['TRANSLATED'][
                   self.script_name.text()][k][1:-1] != '':
                translated_count += 1
        self.progress_file_label.setText("%s / %s" % (translated_count, total_txt))
        self.xml_progress.setValue(int(translated_count / total_txt * 100))

    def compute_global_progress(self):
        script_data = self.data[self.current_game].script_data['TRANSLATED']
        total_script = 0
        translated_count = 0
        for scripts in script_data:
            total_script += len(self.data[self.current_game].script_data['TRANSLATED'][scripts])
            curr_total_scripts = len(self.data[self.current_game].script_data['TRANSLATED'][scripts])
            for k in range(curr_total_scripts):
                if self.data[self.current_game].script_data['TRANSLATED'][scripts][k][1:-1] != '':
                    translated_count += 1
        self.global_progress_label.setText("%s / %s" % (translated_count, total_script))
        self.overall_progress.setValue(int(translated_count / total_script * 100))

    def modification_has_been_made(self, tagname):

        prev_script_index = self.txt_files.currentItem().text()
        translated_backup = self.data[self.current_game].script_data[tagname][self.script_name.text()][int(prev_script_index)]
        self.data[self.current_game].script_data[tagname][self.script_name.text()][int(prev_script_index)] = '\n' + self.plaintexts[tagname].toPlainText().strip('\n').strip() + '\n'

        xml_file = self.script_name.text()

        xml_file_file = join('script_data', self.current_game,
                             xml_file.split('.')[0], xml_file)
        # open file in binary mode
        f = open(xml_file_file, 'rb')
        # store everything in a variable
        buffer = f.read()
        # close the file
        f.close()
        # decode the utf-16-le encoding, in order to be able to manipulate the actual content
        buffer = buffer.decode('utf-16-le')
        # get the index of the first line of script in the buffer
        trad_begin = buffer.find('<'+tagname+' N°') + len('<'+tagname+' N°')
        trad_end = buffer.find('</'+tagname+' N°') + len('</'+tagname+' N°') + 4

        index = 0
        while trad_begin != -1 and trad_end != -1:
            short_key = get_key(buffer, trad_begin)  # '001'

            while buffer[trad_begin] != '>':
                trad_begin += 1
            trad_begin += 1

            if buffer[trad_begin:trad_end] != self.data[self.current_game].script_data[tagname][xml_file][index] + '</'+tagname+' N°' + short_key + '>':
                answer = QMessageBox.question(self,
                                              'Fichier non sauvegardé',
                                              'Certains fichiers n\'ont pas été '
                                              'sauvegardé. Voulez vous sauvegarder ?',
                                              QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel,
                                              QMessageBox.Cancel)

                if answer == QMessageBox.Save:
                    return 1
                elif answer == QMessageBox.Discard:
                    self.data[self.current_game].script_data[tagname][
                        self.script_name.text()][int(prev_script_index)] = translated_backup
                    return 0
                elif answer == QMessageBox.Cancel:
                    return 2

            if index == self.txt_files.count() - 1:
                break
            trad_begin = buffer.find('<'+tagname+' N°', trad_begin) + len(
                '<'+tagname+' N°')
            trad_end = buffer.find('</'+tagname+' N°', trad_begin) + len(
                '</'+tagname+' N°') + 4
            index += 1

        return 3

    def go_prev_script(self):
        if self.txt_files.currentRow() > 0:
            self.txt_files.setCurrentItem(self.txt_files.item(self.txt_files.currentRow() - 1))

    def go_next_script(self):
        if self.txt_files.currentRow() < self.txt_files.count() - 1:
            self.txt_files.setCurrentItem(self.txt_files.item(self.txt_files.currentRow() + 1))

    def check_line_len(self):

        blockText = self.translated.toPlainText().split('\n')
        cursor = self.translated.textCursor()

        w_line = find_w_line(cursor, blockText)
        to_remove = find_to_remove(w_line[:cursor.columnNumber()])

        self.line_count.display(cursor.columnNumber() - to_remove)

        if length_is_okay(self.translated.toPlainText()):
            self.check_line_icon.setPixmap(QPixmap('img/ok.jpeg'))
        else:
            self.check_line_icon.setPixmap(QPixmap('img/error.png'))
            
    def update_line_len(self):

        blockText = self.translated.toPlainText().split('\n')
        cursor = self.translated.textCursor()

        w_line = find_w_line(cursor, blockText)
        to_remove = find_to_remove(w_line[:cursor.columnNumber()])

        self.line_count.display(cursor.columnNumber() - to_remove)

    def copy_from_original_func(self):
        self.translated.setPlainText(self.original.toPlainText())

    def copy_from_japanese_func(self):
        self.translated.setPlainText(self.japanese.toPlainText())

    def save(self):
        """
        Saves into xml files
        """

        for tagname in ('TRANSLATED', 'COMMENT'):

            if self.current_game == '':
                return
            prev_script_index = self.txt_files.currentItem().text()
            self.data[self.current_game].script_data[tagname][self.script_name.text()][int(prev_script_index)] = '\n' + self.plaintexts[tagname].toPlainText().strip('\n').strip() + '\n'

            # compute file progress
            self.compute_file_progress()
            self.compute_global_progress()

            xml_file = self.script_name.text()

            xml_file_file = join('script_data', self.current_game, xml_file.split('.')[0], xml_file)
            # open file in binary mode
            f = open(xml_file_file, 'rb')
            # store everything in a variable
            buffer = f.read()
            # close the file
            f.close()
            # decode the utf-16-le encoding, in order to be able to manipulate the actual content
            buffer = buffer.decode('utf-16-le')
            # get the index of the first line of script in the buffer
            trad_begin = buffer.find('<'+tagname+' N°') + len('<'+tagname+' N°')
            trad_end = buffer.find('</'+tagname+' N°') + len('</'+tagname+' N°') + 4

            index = 0
            while trad_begin != -1 and trad_end != -1:
                short_key = get_key(buffer, trad_begin)  # '001'

                while buffer[trad_begin] != '>':
                    trad_begin += 1
                trad_begin += 1

                buffer = buffer.replace(buffer[trad_begin:trad_end], self.data[self.current_game].script_data[tagname][xml_file][index] + '</'+tagname+' N°' + short_key + '>')

                if index == self.txt_files.count() - 1:
                    break
                trad_begin = buffer.find('<'+tagname+' N°', trad_begin) + len('<'+tagname+' N°')
                trad_end = buffer.find('</'+tagname+' N°', trad_begin) + len('</'+tagname+' N°') + 4
                index += 1

            with open(xml_file_file, 'wb') as f:
                f.write(buffer.encode('utf-16-le'))

    def jisho_search(self):
        self.jp_text.setDisabled(True)
        self.search_btn.setDisabled(True)
        self.jp_result.setPlainText('Recherche en cours...')
        jp_text = self.jp_text.text()
        self.worker.set_jp_text(jp_text)
        self.worker.done.connect(self.jisho_search_done)
        self.worker.start()

    def jisho_search_done(self, data):
        s = str()
        for part in data:
            s += "(%s) %s : %s = %s\n\n" % (
                part[2], part[0], part[1], part[3][0])

        self.jp_result.setPlainText(s)
        self.jp_text.setDisabled(False)
        self.search_btn.setDisabled(False)

    def closeEvent(self, event):
        if self.current_game == '':
            event.accept()
            return
        ret = self.modification_has_been_made('TRANSLATED')

        if ret == 1:
            self.save()
            event.accept()
        elif ret == 2:
            event.ignore()
        elif ret == 0:
            self.discard = True
            event.accept()
        else:
            ret = self.modification_has_been_made('COMMENT')

            if ret == 1:
                self.save()
                event.accept()
            elif ret == 2:
                event.ignore()
            elif ret == 0:
                self.discard = True
                event.accept()


app = QApplication(argv)
w = Ui_MainWindow()
w.show()
exit(app.exec_())
