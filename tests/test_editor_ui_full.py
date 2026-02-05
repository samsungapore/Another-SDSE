import os
from pathlib import Path

import pytest


def _write_po(path: Path, *, entries: list[tuple[str, str, str]]):
    # entries: (ctx, id, str)
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
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_editor_ui_po_flow(tmp_path: Path, monkeypatch):
    # Create working dir with script_data.
    root = tmp_path
    (root / 'script_data' / 'dr1').mkdir(parents=True)

    po1 = root / 'script_data' / 'dr1' / 'e00_000_000.po'
    po2 = root / 'script_data' / 'dr1' / 'e00_000_001.po'

    # Duplicate original line 'Hello' across scripts to populate dupes.
    _write_po(po1, entries=[('0001 | MAKOTO', 'Hello', 'Bonjour'), ('0002', '[EMPTY_LINE]', '[EMPTY_LINE]')])
    _write_po(po2, entries=[('0001 | MAKOTO', 'Hello', ''), ('0002', 'World', '')])

    monkeypatch.chdir(root)

    import editor_ui

    # ensure JSON writes go to temp
    editor_ui.expanduser = lambda p: str(root / 'sdse_data_file.json')

    w = editor_ui.Ui_MainWindow()

    assert 'dr1' in w.games

    # Switch to first script and trigger change_text.
    w.switch_file(str(po1), game='dr1', line_index=0)

    # Basic UI actions
    w.open_ui_launch()
    w.show_search_ui()
    w.close_search_ui()
    w.close_open_ui()

    # Navigate
    w.go_next_script()
    w.go_prev_script()

    # Editing helpers
    w.copy_from_original_func()
    w.copy_from_japanese_func()

    # Line length checks
    w.check_line_len()
    w.update_line_len()

    # Search
    w.search_ui.search_le.setText('hello')
    w.search_in_all_database()
    w.show_search_results(0)

    # Go to script via search result
    item = w.search_ui.file_list.item(0)
    w.go_to_script(item)

    # Jisho search (thread stub runs synchronously)
    w.jp_text.setText('日本語')
    w.jisho_search()

    # Update database with dupes
    w.translated.setPlainText('Bonjour')
    w.comment.setPlainText('note')
    w.update_script_database('dr1', str(po1), 0)

    # Save should update .po on disk.
    w.save()

    # JSON operations
    w.put_in_json()
    w.delete_json_conf_file()

    # closeEvent paths
    class Ev:
        def __init__(self):
            self.accepted = False
            self.ignored = False

        def accept(self):
            self.accepted = True

        def ignore(self):
            self.ignored = True

    ev = Ev()
    w.closeEvent(ev)

    # Also cover main() (exit is imported in editor_ui; patch it so it raises SystemExit)
    monkeypatch.setattr(editor_ui, 'exit', lambda code=0: (_ for _ in ()).throw(SystemExit(code)))
    with pytest.raises(SystemExit):
        editor_ui.main()


def test_editor_ui_load_data_missing_script_data(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    import editor_ui

    # ensure JSON writes go to temp
    editor_ui.expanduser = lambda p: str(tmp_path / 'sdse_data_file.json')

    with pytest.raises(SystemExit):
        editor_ui.Ui_MainWindow()


def test_editor_ui_check_files_modifications_branches(tmp_path: Path, monkeypatch):
    (tmp_path / 'script_data' / 'dr1').mkdir(parents=True)
    po = tmp_path / 'script_data' / 'dr1' / 'e00_000_000.po'
    _write_po(po, entries=[('0001', 'Hello', '')])

    monkeypatch.chdir(tmp_path)

    import editor_ui

    editor_ui.expanduser = lambda p: str(tmp_path / 'sdse_data_file.json')

    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(po), game='dr1', line_index=0)

    # Force branches by monkeypatching modification_has_been_made
    w.modification_has_been_made = lambda tag: 1
    assert w.check_files_modifications() is True

    w.modification_has_been_made = lambda tag: 2
    assert w.check_files_modifications() is False

    w.modification_has_been_made = lambda tag: 0
    assert w.check_files_modifications() is True

    w.modification_has_been_made = lambda tag: 3
    assert w.check_files_modifications() is True
