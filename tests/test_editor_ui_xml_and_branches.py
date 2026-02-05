import runpy
from pathlib import Path

import pytest


def _write_xml(path: Path, *, original: str, translated: str, comment: str = ""):
    txt = (
        f"<ORIGINAL N°001>\n{original}\n</ORIGINAL N°001>\n"
        f"<TRANSLATED N°001>\n{translated}\n</TRANSLATED N°001>\n"
        f"<COMMENT N°001>\n{comment}\n</COMMENT N°001>\n"
    )
    path.write_bytes(txt.encode('utf-16-le'))


def _write_po(path: Path, *, entries: list[tuple[str, str, str]]):
    lines = [
        'msgid ""',
        'msgstr ""',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '',
    ]
    for ctx, mid, mstr in entries:
        lines += [
            '#. JP',
            '# note',
            f'msgctxt "{ctx}"',
            f'msgid "{mid}"',
            f'msgstr "{mstr}"',
            '',
        ]
    path.write_text("\n".join(lines) + "\n", encoding='utf-8')


def test_editor_ui_misc_branches(tmp_path: Path, monkeypatch, capsys):
    root = tmp_path
    (root / 'script_data' / 'dr1xml').mkdir(parents=True)
    (root / 'script_data' / 'dr1po').mkdir(parents=True)

    # XML files (also include one that triggers the "else" branch in tree view)
    xml1 = root / 'script_data' / 'dr1xml' / 'e00_000_000.xml'
    xml2 = root / 'script_data' / 'dr1xml' / '11_Report.xml'
    _write_xml(xml1, original='Hello', translated='Bonjour', comment='c')
    _write_xml(xml2, original='Menu', translated='MenuFR', comment='')

    # PO file
    po1 = root / 'script_data' / 'dr1po' / 'e00_000_000.po'
    _write_po(po1, entries=[('0001 | NO NAME', 'Hello', 'Bonjour')])

    monkeypatch.chdir(root)

    import editor_ui

    # Cover read_json exception path (lines 84-85)
    monkeypatch.setattr(editor_ui, 'load_json_file', lambda *_a, **_kw: (_ for _ in ()).throw(ValueError('bad')))
    w = editor_ui.Ui_MainWindow()
    assert 'Could not read json.' in capsys.readouterr().out

    # delete_json_conf_file else branch
    editor_ui.expanduser = lambda p: str(root / 'missing.json')
    w.delete_json_conf_file()

    # load_data: empty folder returns (cover len==0)
    (root / 'script_data_empty').mkdir()

    # check_files_modifications branches for COMMENT
    w.modification_has_been_made = lambda tag: 3 if tag == 'TRANSLATED' else 2
    assert w.check_files_modifications() is False
    w.modification_has_been_made = lambda tag: 3 if tag == 'TRANSLATED' else 0
    assert w.check_files_modifications() is True

    # restore original method for later assertions
    w.modification_has_been_made = editor_ui.Ui_MainWindow.modification_has_been_made.__get__(w)

    # reload_ui early return when check_files_modifications False
    w.current_game = 'dr1xml'
    w.check_files_modifications = lambda: False
    w.reload_ui()

    # find_ppath / find_script_path failures
    assert w.find_ppath('does-not-exist') is False
    assert w.find_script_path('does-not-exist') == 'does-not-exist'

    # Switch to PO file and cover speaker==NO NAME and japanese IndexError
    w.switch_file(str(po1), game='dr1po', line_index=0)
    w.data['dr1po'].script_data['SPEAKER'][str(po1)] = ['NO NAME']
    w.data['dr1po'].script_data['JAPANESE'][str(po1)] = []
    w.change_text(None, None)

    # script_database_changed for PO tag variants
    for tag in ('SPEAKER', 'JAPANESE', 'COMMENT', 'ORIGINAL', 'TRANSLATED'):
        w.script_database_changed(tag)

    # force check_line_len error branch
    w.translated.setPlainText('x' * 100)
    w.check_line_len()

    # save() current_game == ''
    w.current_game = ''
    w.save()

    # save_file keyerror branch for PO
    w.current_game = 'dr1po'
    w.save_file(str(root / 'script_data' / 'dr1po' / 'missing.po'), 'TRANSLATED')

    # XML mode: switch and cover xml save_file + legacy script_database_changed
    w.switch_file(str(xml1), game='dr1xml', line_index=0)
    w.save_file(str(xml1), 'TRANSLATED')
    w.script_database_changed('TRANSLATED')

    # modification_has_been_made: currentItem None
    w.txt_files.clear()
    assert w.modification_has_been_made('TRANSLATED') == 0

    # search_in_all_database early return
    w.current_game = ''
    w.search_in_all_database()


def test_editor_ui_search_exception_branches(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1po').mkdir(parents=True)
    po1 = root / 'script_data' / 'dr1po' / 'e00_000_000.po'
    _write_po(po1, entries=[('0001', 'Hello', 'Bonjour')])

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(po1), game='dr1po', line_index=0)

    # Remove keys to trigger except/except ladder
    del w.data['dr1po'].script_data['JAPANESE']
    del w.data['dr1po'].script_data['COMMENT']

    w.search_ui.search_le.setText('hello')
    w.search_in_all_database()


def test_editor_ui_change_file_and_closeEvent_branches(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1po').mkdir(parents=True)
    po1 = root / 'script_data' / 'dr1po' / 'e00_000_000.po'
    _write_po(po1, entries=[('0001', 'Hello', '')])

    monkeypatch.chdir(root)

    import editor_ui

    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')
    w = editor_ui.Ui_MainWindow()

    # change_file: else branch expand/collapse
    item = editor_ui.QTreeWidgetItem()
    item.setText(0, w.parts[0])
    w.change_file(item, 0)
    item._expanded = True
    w.change_file(item, 0)

    # change_file: script branch + early returns
    game = editor_ui.QTreeWidgetItem()
    game.setText(0, 'dr1po')
    part = editor_ui.QTreeWidgetItem(game)
    part.setText(0, w.parts[0])
    script = editor_ui.QTreeWidgetItem(part)
    script.setText(0, 'missing')

    w.current_game = 'dr1po'
    w.check_files_modifications = lambda: False
    w.change_file(script, 0)  # returns at check_files_modifications

    w.check_files_modifications = lambda: True
    w.find_ppath = lambda *_: False
    w.change_file(script, 0)

    w.find_ppath = lambda *_: True
    w.script_ppath = str(po1)
    w.switch_file = lambda *_a, **_kw: None
    w.change_file(script, 0)

    # restore real switch_file for later closeEvent/save paths
    w.switch_file = editor_ui.Ui_MainWindow.switch_file.__get__(w)

    # go_to_script early returns
    w.search_sepatator = '||'
    class It:
        def text(self):
            return 'x||0'
    w.current_game = 'dr1po'
    w.check_files_modifications = lambda: False
    w.go_to_script(It())
    w.check_files_modifications = lambda: True
    w.find_ppath = lambda *_: False
    w.go_to_script(It())

    # closeEvent branches
    class Ev:
        def __init__(self):
            self.accepted = False
            self.ignored = False
        def accept(self):
            self.accepted = True
        def ignore(self):
            self.ignored = True

    w.current_game = ''
    ev = Ev()
    w.closeEvent(ev)
    assert ev.accepted is True

    w.current_game = 'dr1po'
    w.modification_has_been_made = lambda tag: 2
    ev2 = Ev()
    w.closeEvent(ev2)
    assert ev2.ignored is True

    w.modification_has_been_made = lambda tag: 0
    ev3 = Ev()
    w.closeEvent(ev3)
    assert ev3.accepted is True

    # Ensure a current file is loaded so save() has a currentItem
    w.switch_file(str(po1), game='dr1po', line_index=0)

    w.modification_has_been_made = lambda tag: 1
    ev4 = Ev()
    w.closeEvent(ev4)
    assert ev4.accepted is True


def test_editor_ui_run_as_main(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / 'script_data' / 'dr1po').mkdir(parents=True)
    po1 = root / 'script_data' / 'dr1po' / 'e00_000_000.po'
    _write_po(po1, entries=[('0001', 'Hello', '')])

    monkeypatch.chdir(root)

    # Running as __main__ should execute the guard at the bottom of editor_ui.py.
    with pytest.raises(SystemExit):
        runpy.run_path(str(Path(__file__).parent.parent / 'editor_ui.py'), run_name='__main__')
