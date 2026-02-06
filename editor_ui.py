# -*- coding: utf-8 -*-
import sys
import warnings
warnings.filterwarnings("ignore", message="sipPyTypeDict.*is deprecated")
from PyQt5.QtCore import Qt
from os.path import basename, join, exists, expanduser
from sys import argv, exit, stdout
from pathlib import Path


def resource_path(relative_path):
    """Return absolute path to resource, works for dev and PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)
    return str(Path(base_path) / relative_path)

from PyQt5.QtGui import QPixmap, QIcon, QKeySequence, QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, \
    QTreeWidgetItem, QMessageBox, QShortcut
from os import listdir, remove
from qtpy import uic

from json_file_working import load_json_file, dump_into_json
from save import get_key
from script_analyser import XmlAnalyser, length_is_okay, cleaned_text, \
    find_w_line, find_to_remove
from po_io import update_po_file, read_po, parse_context_speaker
from translator import SearchThread

json_file_name = 'sdse_data_file.json'
VERSION = "1.5"


class Ui_MainWindow(QMainWindow):
    """
    Another SDSE for your pleasure.
    """

    def __init__(self):
        """
        Initialization of the main GUI
        """
        QMainWindow.__init__(self)
        uic.loadUi(resource_path('gui/AnotherSDSE.ui'), self)

        self.setWindowIcon(QIcon(resource_path('img/cropped-avatarmiraiteam.ico')))
        self.setWindowTitle('Another SDSE ' + VERSION)

        # dupes variable
        self.data = dict()
        self.dupes = dict()
        self.data_modified_in_dupes = False
        self.dupes_files_to_save = list()
        self.script_ppath = None
        self.search_sepatator = '||'

        self.search_data = dict()

        self.pixmap_line_len = None

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
        uic.loadUi(resource_path('gui/open_dialog.ui'), self.open_ui)

        self.search_ui = QDialog()
        uic.loadUi(resource_path('gui/search_ui.ui'), self.search_ui)

        self.load_data()
        self.init_open_ui_tree_view()
        self.create_dupes_database()
        self.set_signals()
        self.set_shortcuts()
        try:
            self.read_json()
        except:
            print('Could not read json.')

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

        # DELETE JSON CONF FILE
        self.delete_json_file.triggered.connect(self.delete_json_conf_file)

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

        ######################## SEARCH GUI PART ########################

        self.search_ui.search_le.returnPressed.connect(
            self.search_in_all_database)
        self.search_ui.file_list.currentRowChanged.connect(
            self.show_search_results)

        self.search_ui.file_list.itemDoubleClicked.connect(self.go_to_script)

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

        self.search_in_data.clicked.connect(self.show_search_ui)

    def set_shortcuts(self):
        open_sc = QShortcut(QKeySequence(QKeySequence.Open), self)
        save_sc = QShortcut(QKeySequence(QKeySequence.Save), self)
        copy_from_original_sc = QShortcut(QKeySequence(QKeySequence.Print),
                                          self)
        go_prev_script_sc = QShortcut(
            QKeySequence(QKeySequence.MoveToPreviousPage), self)
        go_next_script_sc = QShortcut(
            QKeySequence(QKeySequence.MoveToNextPage), self)

        open_sc.activated.connect(self.open_ui_launch)
        save_sc.activated.connect(self.save)
        copy_from_original_sc.activated.connect(self.copy_from_original_func)
        go_prev_script_sc.activated.connect(self.go_prev_script)
        go_next_script_sc.activated.connect(self.go_next_script)

    def read_json(self):

        if load_json_file(expanduser('~/' + json_file_name)) == {}:
            with open(expanduser('~/' + json_file_name), 'w') as f:
                f.write('\n')
        else:
            data = load_json_file(expanduser('~/' + json_file_name))
            if data != {} and 'name' in data.keys():
                self.switch_file(data['name'], data['game'], data['line_index'])

    def delete_json_conf_file(self):
        if exists(expanduser('~/' + json_file_name)):
            remove(expanduser('~/' + json_file_name))
            QMessageBox.information(self, 'Fichier JSON',
                                    'Le fichier JSON a bien été supprimé de'
                                    ' votre ordinateur.')
        else:
            QMessageBox.warning(self, 'Fichier JSON',
                                'Le fichier JSON n\'est pas présent sur'
                                ' votre ordinateur.')

    def put_in_json(self):
        dump_into_json(
            expanduser('~/' + json_file_name),
            {
                'name': self.script_ppath,
                'game': self.current_game,
                'line_index': self.txt_files.currentRow()
            })

    def load_data(self):
        """
        Loads the data present in /script_data
        """

        if not exists('./script_data/'):
            QMessageBox.warning(self, 'Error: No script data',
                                'No "script_data" folder found. No script could be loaded.\n'
                                'Please create a directory "script_data" and create in this dir another dir, '
                                'for example named "dr1" with the xml files in this directory.')
            exit(0)
        try:
            game_dirs = listdir('./script_data/')
        except FileNotFoundError:
            # Defensive: if the folder disappears between exists() and listdir().
            exit(0)

        if len(game_dirs) == 0:
            return

        percent = 100 / (len(game_dirs) * 6)
        total = percent
        to_retrieve = ('TRANSLATED', 'ORIGINAL', 'JAPANESE', 'COMMENT',
                       'SPEAKER')

        for game in game_dirs:
            stdout.write('\r' + str(round(total, 2)) + ' %')
            total += percent
            self.data[game] = XmlAnalyser("./script_data/" + game)

            for tagname in to_retrieve:
                stdout.write('\r' + str(round(total, 2)) + ' %')
                total += percent
                self.data[game].analyse_scripts(tagname)
            print('\r' + game + ' loaded.')
            self.games.append(game)

    def create_dupes_database(self):
        for game in self.games:
            self.dupes[game] = dict()
            scripts = self.data[game].script_data['ORIGINAL']

            tmp = dict()
            for file in scripts:
                i = 0
                for line in scripts[file]:
                    if line not in tmp.keys():
                        tmp[line] = [{'script_name': file, 'line_index': i}]
                    else:
                        tmp[line].append(
                            {'script_name': file, 'line_index': i})
                        self.dupes[game][line] = tmp[line]
                    i += 1

    def check_files_modifications(self):
        ret = self.modification_has_been_made('TRANSLATED')

        if ret == 1:
            self.save()
        elif ret == 2:
            return False
        elif ret == 0:
            self.discard = True
        else:
            ret = self.modification_has_been_made('COMMENT')

            if ret == 1:
                self.save()
            elif ret == 2:
                return False
            elif ret == 0:
                self.discard = True
        return True

    def reload_ui(self, update_curr_text=True):
        """
        Reload data from XML
        """

        if self.current_game != '':

            if not self.check_files_modifications():
                return

            self.data[self.current_game] = XmlAnalyser(
                "./script_data/" + self.current_game)
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
                elem = basename(elem)
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
            self.open_ui.treeWidget.setCurrentItem(
                self.open_ui.treeWidget.itemAt(0, 0))
        self.open_ui.treeWidget.setFocus()
        self.open_ui.exec_()

    def show_search_ui(self):
        self.search_ui.show()
        self.search_ui.exec_()

    def close_open_ui(self):
        """
        this method closes the "open gui"
        """
        self.open_ui.close()
        self.setFocus()

    def close_search_ui(self):
        self.search_ui.close()
        self.setFocus()

    def switch_file(self, script_name, game=None, line_index=0):
        """
        Switch file
        :param script_name: full path
        :param game: item.parent().parent().text(0)
        :param line_index:
        """
        if not self.script_name.text() == '':
            self.previous_script_name = self.script_name.text()
        else:
            self.previous_script_name = basename(script_name)

        self.script_name.setText(basename(script_name))
        self.setWindowTitle(basename(script_name) + ' - Another SDSE ' + VERSION)

        if not self.current_game == '':
            self.previous_game = self.current_game
        else:
            if game is not None:
                self.previous_game = game
        if game is not None:
            self.current_game = game
        self.overall_progress_label.setText(
            'Progress on ' + self.current_game)
        self.script_ppath = script_name
        # set the script files in the window
        txt_files = self.data[self.current_game].script_data['ORIGINAL'][script_name]
        list_of_txt_index = [str(i) for i in range(len(txt_files))]
        self.file_has_changed = True
        self.txt_files.clear()
        self.txt_files.addItems(list_of_txt_index)
        self.txt_files.setCurrentItem(self.txt_files.item(int(line_index)))
        self.reload_ui()

    def change_file(self, item, column):
        if item.text(column) not in self.parts and item.text(
                column) not in self.games:
            self.close_open_ui()

            if self.current_game != '':
                if not self.check_files_modifications():
                    return

            if not self.find_ppath(item.text(column)):
                return

            self.switch_file(self.script_ppath, item.parent().parent().text(0))
        else:
            if item.isExpanded():
                self.open_ui.treeWidget.collapseItem(item)
            else:
                self.open_ui.treeWidget.expandItem(item)

            self.open_ui.treeWidget.scrollToItem(item)

    def find_ppath(self, script_name):
        for game in self.games:
            for ppath in self.data[game].script_data['ORIGINAL']:
                if ppath.find(script_name) != -1:
                    self.script_ppath = ppath
                    return True
        QMessageBox.warning(QMessageBox(), self, "Error", "Couldn't load script", QMessageBox.Ok)
        return False

    def find_script_path(self, script_name):
        for game in self.games:
            for ppath in self.data[game].script_data['ORIGINAL']:
                if ppath.find(script_name) != -1:
                    return ppath
        QMessageBox.warning(QMessageBox(), self, "Error", "Couldn't load script", QMessageBox.Ok)
        return script_name

    def change_text(self, item, previous_item):
        if item is None:
            item = self.txt_files.item(0)
        script_index = item.text()

        # update data if previous item exists
        if previous_item is not None:
            prev_script_index = previous_item.text()
            if self.file_has_changed:
                if not self.discard:
                    self.update_script_database(self.previous_game,
                                                self.find_script_path(self.previous_script_name),
                                                prev_script_index)
                else:
                    self.discard = False
                self.file_has_changed = False
            else:
                if not self.discard:
                    self.update_script_database(self.current_game,
                                                self.script_ppath,
                                                prev_script_index)
                else:
                    self.discard = False

        translated_text = self.data[self.current_game].script_data['TRANSLATED'][self.script_ppath][int(script_index)][1:-1]
        original_text = self.data[self.current_game].script_data['ORIGINAL'][self.script_ppath][int(script_index)][1:-1]
        comment_text = self.data[self.current_game].script_data['COMMENT'][self.script_ppath][int(script_index)][1:-1]
        try:
            speaker = self.data[self.current_game].script_data['SPEAKER'][self.script_ppath][int(script_index)]
        except IndexError:
            speaker = 'System Text'
        if speaker == 'NO NAME':
            speaker = 'Narrateur'
        else:
            speaker = speaker.lower().split(' ')
            tmp = str()
            for word in speaker:
                tmp += word.capitalize() + ' '
            speaker = tmp[:-1]
        try:
            japanese_text = self.data[self.current_game].script_data['JAPANESE'][self.script_ppath][int(script_index)][1:-1]
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

        if self.script_database_changed():
            self.setWindowTitle(
                self.script_name.text() + '* - Another SDSE ' + VERSION)
        else:
            self.setWindowTitle(
                self.script_name.text() + ' - Another SDSE ' + VERSION)

    def update_script_database(self, game, script_name, prev_script_index):
        # retrieving texts data
        original_line = self.data[game].script_data['ORIGINAL'][script_name][int(prev_script_index)]
        translated_text_to_save = '\n%s\n' % (
            self.translated.toPlainText().strip('\n').strip())
        comment_text_to_save = '\n%s\n' % (
            self.comment.toPlainText().strip('\n').strip())

        # check if the text modified belongs to the dupes database
        if original_line in self.dupes[game].keys():
            for element_to_save in self.dupes[game][original_line]:
                if element_to_save['script_name'] != script_name:
                    self.data_modified_in_dupes = True
                self.data[game].script_data['TRANSLATED'][element_to_save['script_name']][element_to_save['line_index']] = translated_text_to_save
                self.dupes_files_to_save.append(element_to_save['script_name'])
            if self.data_modified_in_dupes:
                self.dupes_files_to_save = list(set(self.dupes_files_to_save))
            else:
                self.dupes_files_to_save = list()
        else:
            self.data[game].script_data['TRANSLATED'][script_name][
                int(prev_script_index)] = translated_text_to_save
            self.data[game].script_data['COMMENT'][script_name][
                int(prev_script_index)] = comment_text_to_save

    def compute_file_progress(self):
        translated_count = 0
        total_txt = len(self.data[self.current_game].script_data['TRANSLATED'][self.script_ppath])

        for k in range(total_txt):
            if self.data[self.current_game].script_data['TRANSLATED'][self.script_ppath][k][1:-1] != '':
                translated_count += 1

        self.progress_file_label.setText("%s / %s" % (translated_count, total_txt))
        self.xml_progress.setValue(int(translated_count / total_txt * 100))

    def compute_global_progress(self):
        script_data = self.data[self.current_game].script_data['TRANSLATED']
        total_script = 0
        translated_count = 0
        for scripts in script_data:
            total_script += len(
                self.data[self.current_game].script_data['TRANSLATED'][scripts])
            curr_total_scripts = len(
                self.data[self.current_game].script_data['TRANSLATED'][scripts])
            for k in range(curr_total_scripts):
                if self.data[self.current_game].script_data['TRANSLATED'][scripts][k][1:-1] != '':
                    translated_count += 1
        self.global_progress_label.setText("%s / %s" % (translated_count, total_script))
        self.overall_progress.setValue(int(translated_count / total_script * 100))

    def script_database_changed(self, tagname='TRANSLATED'):

        # DRAT 1.5.2+ (.po)
        if self.script_ppath.lower().endswith('.po'):
            entries = read_po(Path(self.script_ppath))

            disk_lines = []
            if tagname == 'SPEAKER':
                for e in entries:
                    _, sp = parse_context_speaker(e.msgctxt)
                    disk_lines.append(sp or '')
            elif tagname == 'JAPANESE':
                for e in entries:
                    disk_lines.append('\n' + "\n".join(e.extracted_comments) + '\n')
            elif tagname == 'COMMENT':
                for e in entries:
                    disk_lines.append('\n' + "\n".join(e.translator_comments) + '\n')
            elif tagname == 'ORIGINAL':
                for e in entries:
                    o = '' if e.msgid == '[EMPTY_LINE]' else e.msgid
                    disk_lines.append('\n' + o + '\n')
            else:  # TRANSLATED
                for e in entries:
                    t = '' if e.msgstr == '[EMPTY_LINE]' else e.msgstr
                    disk_lines.append('\n' + t + '\n')

            mem_lines = self.data[self.current_game].script_data[tagname][self.script_ppath]
            return disk_lines != mem_lines

        # Legacy XML mode
        # open file in binary mode
        f = open(self.script_ppath, 'rb')
        # store everything in a variable
        buffer = f.read()
        # close the file
        f.close()
        # decode the utf-16-le encoding, in order to be able to manipulate the actual content
        buffer = buffer.decode('utf-16-le')
        # get the index of the first line of script in the buffer
        trad_begin = buffer.find('<' + tagname + ' N°') + len(
            '<' + tagname + ' N°')
        trad_end = buffer.find('</' + tagname + ' N°') + len(
            '</' + tagname + ' N°') + 4
        xml_file_data = self.data[self.current_game].script_data[tagname][self.script_ppath]

        index = 0
        while trad_begin != -1 and trad_end != -1:
            short_key = get_key(buffer, trad_begin)  # '001'

            while buffer[trad_begin] != '>':
                trad_begin += 1
            trad_begin += 1

            if buffer[trad_begin:trad_end] != self.data[self.current_game].script_data[tagname][self.script_ppath][index] + '</' + tagname + ' N°' + short_key + '>':
                return True

            if index == len(xml_file_data) - 1:
                break
            trad_begin = buffer.find('<' + tagname + ' N°', trad_begin) + len('<' + tagname + ' N°')
            trad_end = buffer.find('</' + tagname + ' N°', trad_begin) + len('</' + tagname + ' N°') + 4
            index += 1

        return False

    def modification_has_been_made(self, tagname):

        if self.txt_files.currentItem() is None:
            return 0
        prev_script_index = self.txt_files.currentItem().text()
        translated_backup = self.data[self.current_game].script_data[tagname][self.script_ppath][int(prev_script_index)]
        self.data[self.current_game].script_data[tagname][self.script_ppath][int(prev_script_index)] = '\n' + self.plaintexts[tagname].toPlainText().strip('\n').strip() + '\n'

        # DRAT 1.5.2+ (.po)
        if self.script_ppath.lower().endswith('.po'):
            entries = read_po(Path(self.script_ppath))

            disk_lines = []
            if tagname == 'COMMENT':
                for e in entries:
                    disk_lines.append('\n' + "\n".join(e.translator_comments) + '\n')
            else:  # TRANSLATED
                for e in entries:
                    t = '' if e.msgstr == '[EMPTY_LINE]' else e.msgstr
                    disk_lines.append('\n' + t + '\n')

            mem_lines = self.data[self.current_game].script_data[tagname][self.script_ppath]
            if disk_lines != mem_lines:
                answer = QMessageBox.question(
                    self,
                    'Fichier non sauvegardé',
                    'Certains fichiers n\'ont pas été sauvegardé. Voulez vous sauvegarder ?',
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Cancel
                )

                if answer == QMessageBox.Save:
                    return 1
                elif answer == QMessageBox.Discard:
                    self.data[self.current_game].script_data[tagname][self.script_ppath][int(prev_script_index)] = translated_backup
                    return 0
                elif answer == QMessageBox.Cancel:
                    return 2

            return 3

        f = open(self.script_ppath, 'rb')
        # store everything in a variable
        buffer = f.read()
        # close the file
        f.close()
        # decode the utf-16-le encoding, in order to be able to manipulate the actual content
        buffer = buffer.decode('utf-16-le')
        # get the index of the first line of script in the buffer
        trad_begin = buffer.find('<' + tagname + ' N°') + len('<' + tagname + ' N°')
        trad_end = buffer.find('</' + tagname + ' N°') + len('</' + tagname + ' N°') + 4
        xml_file_data = self.data[self.current_game].script_data[tagname][self.script_ppath]

        index = 0
        while trad_begin != -1 and trad_end != -1:
            short_key = get_key(buffer, trad_begin)  # '001'

            while buffer[trad_begin] != '>':
                trad_begin += 1
            trad_begin += 1

            if buffer[trad_begin:trad_end] != self.data[self.current_game].script_data[tagname][self.script_ppath][index] + '</' + tagname + ' N°' + short_key + '>':
                answer = QMessageBox.question(
                    self,
                    'Fichier non sauvegardé',
                    'Certains fichiers n\'ont pas été sauvegardé. Voulez vous sauvegarder ?',
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Cancel
                )

                if answer == QMessageBox.Save:
                    return 1
                elif answer == QMessageBox.Discard:
                    self.data[self.current_game].script_data[tagname][self.script_ppath][int(prev_script_index)] = translated_backup
                    return 0
                elif answer == QMessageBox.Cancel:
                    return 2

            if index == len(xml_file_data) - 1:
                break
            trad_begin = buffer.find('<' + tagname + ' N°', trad_begin) + len('<' + tagname + ' N°')
            trad_end = buffer.find('</' + tagname + ' N°', trad_begin) + len('</' + tagname + ' N°') + 4
            index += 1

        return 3

    def go_prev_script(self):
        if self.txt_files.currentRow() > 0:
            self.txt_files.setCurrentItem(
                self.txt_files.item(self.txt_files.currentRow() - 1))

    def go_next_script(self):
        if self.txt_files.currentRow() < self.txt_files.count() - 1:
            self.txt_files.setCurrentItem(
                self.txt_files.item(self.txt_files.currentRow() + 1))

    def check_line_len(self):

        blockText = self.translated.toPlainText().split('\n')
        cursor = self.translated.textCursor()

        w_line = find_w_line(cursor, blockText)
        to_remove = find_to_remove(w_line[:cursor.columnNumber()])

        self.line_count.display(cursor.columnNumber() - to_remove)

        if length_is_okay(self.translated.toPlainText()):
            if self.pixmap_line_len is None or self.pixmap_line_len == 'error':
                self.check_line_icon.setPixmap(QPixmap(resource_path('img/ok.jpeg')))
                self.pixmap_line_len = 'ok'
        else:
            if self.pixmap_line_len is None or self.pixmap_line_len == 'ok':
                self.check_line_icon.setPixmap(QPixmap(resource_path('img/error.png')))
                self.pixmap_line_len = 'error'

    def update_line_len(self):

        blockText = self.translated.toPlainText().split('\n')
        cursor = self.translated.textCursor()

        w_line = find_w_line(cursor, blockText)
        to_remove = find_to_remove(w_line[:cursor.columnNumber()])

        self.line_count.display(cursor.columnNumber() - to_remove)

    def copy_from_original_func(self):
        self.translated.setPlainText(self.original.toPlainText())
        self.translated.moveCursor(QTextCursor.EndOfLine)

    def copy_from_japanese_func(self):
        self.translated.setPlainText(self.japanese.toPlainText())
        self.translated.moveCursor(QTextCursor.EndOfLine)

    def save(self):
        """
        Saves into xml files
        """

        for tagname in ('TRANSLATED', 'COMMENT'):

            if self.current_game == '':
                return
            prev_script_index = self.txt_files.currentItem().text()
            self.data[self.current_game].script_data[tagname][self.script_ppath][int(prev_script_index)] = '\n' + self.plaintexts[tagname].toPlainText().strip('\n').strip() + '\n'

            # compute file progress
            self.compute_file_progress()
            self.compute_global_progress()

            if not self.data_modified_in_dupes:
                self.save_file(self.script_ppath, tagname)
            else:
                for xml_file in self.dupes_files_to_save:
                    self.save_file(xml_file, tagname)
                self.data_modified_in_dupes = False
        self.setWindowTitle(self.script_name.text() + ' - Another SDSE ' + VERSION)

    def save_file(self, xml_file, tagname):
        # DRAT 1.5.2+ uses .po files.
        if xml_file.lower().endswith('.po'):
            try:
                po_file_data = self.data[self.current_game].script_data[tagname][xml_file]
            except KeyError:
                print("Key error " + xml_file + ". Dupe issue.")
                return

            # Only TRANSLATED + COMMENT are editable in the UI.
            if tagname == 'TRANSLATED':
                update_po_file(Path(xml_file), translated=po_file_data)
            elif tagname == 'COMMENT':
                update_po_file(Path(xml_file), comment=po_file_data)
            return

        try:
            xml_file_data = self.data[self.current_game].script_data[tagname][xml_file]
            # open file in binary mode
            f = open(xml_file, 'rb')
        except KeyError:
            print("Key error " + xml_file + ". Dupe issue.")
            return
        # store everything in a variable
        buffer = f.read()
        # close the file
        f.close()
        # decode the utf-16-le encoding, in order to be able to manipulate the actual content
        buffer = buffer.decode('utf-16-le')
        # get the index of the first line of script in the buffer
        trad_begin = buffer.find('<' + tagname + ' N°') + len('<' + tagname + ' N°')
        trad_end = buffer.find('</' + tagname + ' N°') + len('</' + tagname + ' N°') + 4

        index = 0
        while trad_begin != -1 and trad_end != -1:
            short_key = get_key(buffer, trad_begin)  # '001'

            while buffer[trad_begin] != '>':
                trad_begin += 1
            trad_begin += 1

            buffer = buffer.replace(buffer[trad_begin:trad_end], xml_file_data[index] + '</' + tagname + ' N°' + short_key + '>')

            if index == len(xml_file_data) - 1:
                break
            trad_begin = buffer.find('<' + tagname + ' N°', trad_begin) + len('<' + tagname + ' N°')
            trad_end = buffer.find('</' + tagname + ' N°', trad_begin) + len('</' + tagname + ' N°') + 4
            index += 1

        try:
            with open(xml_file, 'wb') as f:
                f.write(buffer.encode('utf-16-le'))
        except:
            print("ERROR SAVING " + self.script_ppath)
            return

    def search_in_all_database(self):
        if self.search_ui.search_le.text() == '' or self.current_game == '':
            return

        self.search_ui.file_list.clear()
        self.search_data.clear()

        tmp_search_data = list()
        script = self.data[self.current_game].script_data
        for section in script:
            if section == 'SPEAKER':
                continue
            for file in script[section]:
                i = 0
                for line in script[section][file]:
                    if line.lower().find(self.search_ui.search_le.text().lower()) != -1:
                        if file + self.search_sepatator + str(i) not in tmp_search_data:
                            tmp_search_data.append(file + self.search_sepatator + str(i))
                            self.search_ui.file_list.addItem(file + self.search_sepatator + str(i))
                            try:
                                self.search_data[file] = {
                                    'TRANSLATED': script['TRANSLATED'][file][i],
                                    'ORIGINAL': script['ORIGINAL'][file][i],
                                    'JAPANESE': script['JAPANESE'][file][i],
                                    'index': i
                                }
                            except:
                                try:
                                    self.search_data[file] = {
                                        'TRANSLATED': script['TRANSLATED'][file][i],
                                        'ORIGINAL': script['ORIGINAL'][file][i],
                                        'JAPANESE': script['COMMENT'][file][i],
                                        'index': i
                                    }
                                except:
                                    self.search_data[file] = {
                                        'TRANSLATED': script['TRANSLATED'][file][i],
                                        'ORIGINAL': script['ORIGINAL'][file][i],
                                        'JAPANESE': "",
                                        'index': i
                                    }
                    i += 1
            self.search_ui.file_list.sortItems()
            self.search_ui.file_list.setCurrentRow(0)

    def go_to_script(self, item):
        tmp = item.text().split(self.search_sepatator)

        script_name = tmp[0]
        line_index = tmp[1]

        if script_name not in self.parts and script_name not in self.games:
            self.close_search_ui()

            if self.current_game != '':
                if not self.check_files_modifications():
                    return

            if not self.find_ppath(script_name):
                return
            self.switch_file(self.script_ppath, line_index=line_index)

    def show_search_results(self, row):
        if row == -1:
            return
        s_name = self.search_ui.file_list.item(row).text().split(self.search_sepatator)[0]
        self.search_ui.translated.setPlainText(self.search_data[s_name]['TRANSLATED'][1:-1])
        self.search_ui.original.setPlainText(self.search_data[s_name]['ORIGINAL'][1:-1])
        self.search_ui.japanese.setPlainText(self.search_data[s_name]['JAPANESE'][1:-1])

    def jisho_search(self):
        self.jp_text.setDisabled(True)
        self.search_btn.setDisabled(True)
        self.jp_result.setPlainText('Recherche en cours...')
        jp_text = self.jp_text.text()
        self.worker.set_jp_text(jp_text)
        self.worker.done.connect(self.jisho_search_done)
        self.worker.start()

    def jisho_search_done(self, data):

        self.jp_result.setPlainText("")
        self.jp_text.setDisabled(False)
        self.search_btn.setDisabled(False)

    def closeEvent(self, event):
        if self.current_game == '':
            event.accept()
            return
        ret = self.modification_has_been_made('TRANSLATED')

        if ret == 1:
            self.save()
            self.put_in_json()
            event.accept()
        elif ret == 2:
            event.ignore()
        elif ret == 0:
            self.discard = True
            self.put_in_json()
            event.accept()
        else:
            ret = self.modification_has_been_made('COMMENT')

            if ret == 1:
                self.save()
                self.put_in_json()
                event.accept()
            elif ret == 2:
                event.ignore()
            elif ret == 0:
                self.discard = True
                self.put_in_json()
                event.accept()

        self.put_in_json()


def main():
    app = QApplication(argv)
    w = Ui_MainWindow()
    w.show()
    exit(app.exec_())


if __name__ == '__main__':
    main()
