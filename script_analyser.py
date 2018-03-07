# -*- coding: utf-8 -*-
"""@package SDSE1_analyser
@date Created on oct. 09 16:25 2017
@author samuel_r
"""

import os, sys

from os import walk
from os.path import exists


def find_w_line(cursor, blockText):
    index = 0
    for line in blockText:
        for _ in line:
            if index == cursor.position():
                return line
            index += 1
        if index == cursor.position():
            return line
        index += 1
    return blockText[-1]


def count_rem(w_line, i):
    if w_line.find('>') != -1:
        count = 1
    else:
        count = 0
    while i < len(w_line) and w_line[i] != '>':
        count += 1
        i += 1
    return count, i + 1


def find_to_remove(w_line):
    i = 0
    to_rem = 0
    while i < len(w_line):
        while i < len(w_line) and w_line[i] == '<':
            rem, i = count_rem(w_line, i)
            to_rem += rem
        i += 1
    return to_rem


def cleaned_text(w_line):
    i = 0
    new_line = list()
    while i < len(w_line):
        while i < len(w_line) and w_line[i] == '<':
            var, i = count_rem(w_line, i)
        if i < len(w_line) and w_line[i] != '<':
            new_line.append(w_line[i])
        i += 1
    return ''.join(new_line)


def length_is_okay(line):
    line = cleaned_text(line)
    if line.find('\n') == -1:
        if len(line.replace('\r', '')) > 64:
            return False
        else:
            return True
    else:
        tab = line.split('\n')
        for single_line in tab:
            if len(single_line.replace('\r', '')) > 64:
                return False
        return True


class SDSE1_Analyser:
    def __init__(self, umdimage_path=None):
        self.umdimg_path = umdimage_path
        self.data = []
        self.reacts = []

        self.chapter_correspondence = {
            'e00', 'Prologue',
            'e01', 'Chapitre 1',
            'e02', 'Chapitre 2',
            'e03', 'Chapitre 3',
            'e04', 'Chapitre 4',
            'e05', 'Chapitre 5',
            'e06', 'Chapitre 6',
            'e07', 'Épilogue',
            'e08', 'FTE',
            'e09', 'School Mode'
        }

    def analyse_scripts(self):
        lin_list = os.listdir(self.umdimg_path)
        total_err = 0

        for lin in lin_list:
            if not lin.endswith('.lin'):
                continue
            if not exists(os.path.join(self.umdimg_path, lin, lin.split('.')[0] + '.pak')):
                continue
            for txt in os.listdir(os.path.join(self.umdimg_path, lin, lin.split('.')[0] + '.pak')):
                f = open(os.path.join(self.umdimg_path, lin, lin.split('.')[0] + '.pak', txt), 'rb')
                buffer = f.read()
                f.close()
                try:
                    buffer = buffer.decode('utf-8')
                except UnicodeDecodeError:
                    buffer = buffer.decode('utf-16-le')

                if buffer.find("CLT 1") != -1:
                    self.reacts.append((lin, txt, buffer))
                else:
                    self.data.append(buffer)

        i = 0
        for lin, txt, buffer in self.reacts:
            ok = False
            index = buffer.find('CLT 1') + len('CLT 1>')
            to_find = buffer[index:buffer.find('<CLT>', index)]
            for buf in self.data:
                if buf.find(to_find) != -1:
                    ok = True
            if not ok:
                print(lin + '/' + txt)
            i += 1

def open_file(filename):
    with open(filename, 'rb') as f:
        buf = f.read()

    try:
        buf = buf.decode('utf-8')
    except UnicodeDecodeError:
        buf = buf.decode('utf-16-le')

    return buf


def get_file_script(buf, tag_name='TRANSLATED'):
    translated_s = '<' + tag_name + ' N°'
    end_translated_s = '</' + tag_name

    begin_trad_offset = len(translated_s) + 4
    begin_trad = buf.find(translated_s) + begin_trad_offset
    end_trad = buf.find(end_translated_s)

    xml_script_data = list()

    while begin_trad != -1 and end_trad != -1:

        xml_script_data.append(buf[begin_trad:end_trad])

        if buf.find(translated_s, end_trad) + begin_trad_offset < begin_trad:
            break

        begin_trad = buf.find(translated_s, end_trad) + begin_trad_offset
        end_trad = buf.find(end_translated_s, begin_trad)

    return xml_script_data


def right_len(line):
    # remove <CLT> from line
    line = cleaned_text(line)

    # if single line, directly check len
    if line.find('\n') == -1:
        if len(line) > 64:
            return False
        else:
            return True
    # else, split into an array and check each cell of array
    else:
        tab = line.split('\n')
        for single_line in tab:
            if len(single_line) > 64:
                return False
            else:
                return True


class XmlAnalyser:

    def __init__(self, path):

        self.xml_path = path
        self.script_data = dict()

    def analyse_scripts(self, tag_name='TRANSLATED'):
        new_script_data = dict()

        for dirpath, dirnames, filenames in walk(self.xml_path):
            for filen in filenames:
                if filen.endswith(".xml"):
                    xml_file = os.path.join(dirpath, filen)
                    try:
                        buf = open_file(xml_file)
                    except FileNotFoundError:
                        continue

                    new_script_data[filen] = get_file_script(buf, tag_name)

        self.script_data[tag_name] = new_script_data

    def check_line_length(self):

        xml_list = os.listdir(self.xml_path)

        for xml_dir in xml_list:

            xml_file = os.path.join(self.xml_path, xml_dir, xml_dir + '.xml')
            buf = open_file(xml_file)

            translated_s = '<TRANSLATED N°'
            original_s = '<ORIGINAL N°'
            end_translated_s = '</TRANSLATED'
            end_original_s = '</ORIGINAL'

            begin_trad_offset = len(translated_s) + 4
            o_begin_trad_offset = len(original_s) + 4

            begin_trad = buf.find(translated_s) + begin_trad_offset
            o_begin_trad = buf.find(original_s) + o_begin_trad_offset

            end_trad = buf.find(end_translated_s)
            o_end_trad = buf.find(end_original_s)

            while begin_trad != -1 and end_trad != -1:

                if buf[begin_trad:end_trad] == "\n\n":
                    if not right_len(buf[o_begin_trad:o_end_trad]):
                        print(buf[begin_trad:end_trad])
                else:
                    right_len(buf[begin_trad:end_trad])

                if buf.find(translated_s, end_trad) + begin_trad_offset < begin_trad:
                    break

                begin_trad = buf.find(translated_s, end_trad) + begin_trad_offset
                o_begin_trad = buf.find(original_s, o_end_trad) + o_begin_trad_offset

                end_trad = buf.find(end_translated_s, begin_trad)
                o_end_trad = buf.find(end_original_s, o_begin_trad)

    def show_script_data(self, tag_name='TRANSLATED'):

        for key in self.script_data[tag_name]:

            for line in self.script_data[tag_name][key]:

                if tag_name == 'TRANSLATED':
                    if line != "\n\n":
                        sys.stdout.write(line)
                else:
                    sys.stdout.write(line)
