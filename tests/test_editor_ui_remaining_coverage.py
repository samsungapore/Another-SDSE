from pathlib import Path

import pytest


def _write_xml(path: Path, *, translated: str):
    txt = (
        "<TRANSLATED N°001>\n" + translated + "\n</TRANSLATED N°001>\n"
        "<COMMENT N°001>\n\n</COMMENT N°001>\n"
        "<ORIGINAL N°001>\nORIG\n</ORIGINAL N°001>\n"
    )
    path.write_bytes(txt.encode('utf-16-le'))


def _write_po(path: Path):
    path.write_text(
        "\n".join(
            [
                'msgid ""',
                'msgstr ""',
                '"Content-Type: text/plain; charset=UTF-8\\n"',
                '',
                'msgctxt "0001"',
                'msgid "Hello"',
                'msgstr ""',
                '',
            ]
        )
        + "\n",
        encoding='utf-8',
    )


def test_editor_ui_load_data_branches(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data').mkdir()
    monkeypatch.chdir(root)

    import editor_ui

    # ensure exit raises
    monkeypatch.setattr(editor_ui, 'exit', lambda code=0: (_ for _ in ()).throw(SystemExit(code)))

    # exists says True but listdir fails -> covers FileNotFoundError except
    monkeypatch.setattr(editor_ui, 'exists', lambda p: True)
    monkeypatch.setattr(editor_ui, 'listdir', lambda p: (_ for _ in ()).throw(FileNotFoundError()))

    w = object.__new__(editor_ui.Ui_MainWindow)
    w.data = {}
    w.games = []

    with pytest.raises(SystemExit):
        editor_ui.Ui_MainWindow.load_data(w)


def test_editor_ui_empty_script_data_returns(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data').mkdir()
    monkeypatch.chdir(root)

    import editor_ui

    # Make init not blow up by ensuring script_data exists (empty)
    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')

    # Patch load_json_file so read_json doesn't create weird state
    editor_ui.load_json_file = lambda *_: {}

    w = editor_ui.Ui_MainWindow()
    assert w.games == []


def test_editor_ui_change_text_discard_branches(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1xml').mkdir(parents=True)
    xml = root / 'script_data' / 'dr1xml' / 'e00_000_000.xml'
    _write_xml(xml, translated='Bonjour')

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(xml), game='dr1xml', line_index=0)

    # Cover the two "discard" branches:
    # - when file_has_changed is True (line ~437)
    # - when file_has_changed is False (line ~445)
    item0 = w.txt_files.item(0)

    w.discard = True
    w.file_has_changed = True
    w.change_text(item0, item0)

    w.discard = True
    w.file_has_changed = False
    w.change_text(item0, item0)


def test_editor_ui_star_title_on_unsaved(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1xml').mkdir(parents=True)
    xml = root / 'script_data' / 'dr1xml' / 'e00_000_000.xml'
    _write_xml(xml, translated='Bonjour')

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(xml), game='dr1xml', line_index=0)

    # Make disk != memory so script_database_changed returns True (line 496)
    w.data['dr1xml'].script_data['TRANSLATED'][str(xml)][0] = "\nDIFF\n"
    w.change_text(w.txt_files.item(0), None)


def test_editor_ui_update_script_database_force_line520(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1po').mkdir(parents=True)
    po = root / 'script_data' / 'dr1po' / 'e00_000_000.po'
    _write_po(po)

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(po), game='dr1po', line_index=0)

    # Force dupes structure so original_line is considered a dupe but only within same file
    original_line = w.data['dr1po'].script_data['ORIGINAL'][str(po)][0]
    w.dupes['dr1po'][original_line] = [{'script_name': str(po), 'line_index': 0}]
    w.data_modified_in_dupes = False

    w.translated.setPlainText('X')
    w.comment.setPlainText('')
    w.update_script_database('dr1po', str(po), 0)


def test_editor_ui_modification_has_been_made_question_branches_po(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1po').mkdir(parents=True)
    po = root / 'script_data' / 'dr1po' / 'e00_000_000.po'
    _write_po(po)

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(po), game='dr1po', line_index=0)

    # Create an unsaved change by editing the plaintext widget.
    w.plaintexts['TRANSLATED'].setPlainText('DIFF')

    # Save branch
    monkeypatch.setattr(
        editor_ui.QMessageBox,
        'question',
        staticmethod(lambda *_a, **_kw: editor_ui.QMessageBox.Save),
    )
    assert w.modification_has_been_made('TRANSLATED') == 1

    # Re-create unsaved change
    w.plaintexts['TRANSLATED'].setPlainText('DIFF2')

    # Cancel branch
    monkeypatch.setattr(
        editor_ui.QMessageBox,
        'question',
        staticmethod(lambda *_a, **_kw: editor_ui.QMessageBox.Cancel),
    )
    assert w.modification_has_been_made('TRANSLATED') == 2


def test_editor_ui_modification_has_been_made_xml_branches(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1xml').mkdir(parents=True)
    xml = root / 'script_data' / 'dr1xml' / 'e00_000_000.xml'
    _write_xml(xml, translated='Bonjour')

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(xml), game='dr1xml', line_index=0)

    w.plaintexts['TRANSLATED'].setPlainText('DIFF')

    monkeypatch.setattr(
        editor_ui.QMessageBox,
        'question',
        staticmethod(lambda *_a, **_kw: editor_ui.QMessageBox.Save),
    )
    assert w.modification_has_been_made('TRANSLATED') == 1

    w.plaintexts['TRANSLATED'].setPlainText('DIFF2')

    monkeypatch.setattr(
        editor_ui.QMessageBox,
        'question',
        staticmethod(lambda *_a, **_kw: editor_ui.QMessageBox.Cancel),
    )
    assert w.modification_has_been_made('TRANSLATED') == 2


def test_editor_ui_save_file_xml_keyerror_and_write_error(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1xml').mkdir(parents=True)
    xml = root / 'script_data' / 'dr1xml' / 'e00_000_000.xml'
    _write_xml(xml, translated='Bonjour')

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(xml), game='dr1xml', line_index=0)

    # KeyError branch for xml save_file
    w.save_file(str(root / 'script_data' / 'dr1xml' / 'missing.xml'), 'TRANSLATED')

    # Force write error branch (open() is the built-in)
    import builtins
    orig_open = builtins.open

    def bad_open(path, mode='r', *a, **kw):
        if str(path).endswith('.xml') and 'wb' in mode:
            raise OSError('no')
        return orig_open(path, mode, *a, **kw)

    monkeypatch.setattr(builtins, 'open', bad_open)
    w.save_file(str(xml), 'TRANSLATED')


def test_editor_ui_closeEvent_comment_branches(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1po').mkdir(parents=True)
    po = root / 'script_data' / 'dr1po' / 'e00_000_000.po'
    _write_po(po)

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(po), game='dr1po', line_index=0)

    class Ev:
        def __init__(self):
            self.accepted = False
            self.ignored = False
        def accept(self):
            self.accepted = True
        def ignore(self):
            self.ignored = True

    # Comment save branch
    w.modification_has_been_made = lambda tag: 3 if tag == 'TRANSLATED' else 1
    ev = Ev()
    w.closeEvent(ev)

    # Comment ignore branch
    w.modification_has_been_made = lambda tag: 3 if tag == 'TRANSLATED' else 2
    ev2 = Ev()
    w.closeEvent(ev2)

    # Comment discard branch
    w.modification_has_been_made = lambda tag: 3 if tag == 'TRANSLATED' else 0
    ev3 = Ev()
    w.closeEvent(ev3)
