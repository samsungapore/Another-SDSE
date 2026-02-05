from __future__ import annotations

from pathlib import Path

import editor_ui


def _write_full_xml_two_entries(path: Path):
    def block(tag: str, n: str, content: str) -> str:
        return f"<{tag} N°{n}>\n{content}\n</{tag} N°{n}>\n"

    parts = []
    for n in ("001", "002"):
        parts.append(block("TRANSLATED", n, f"T{n}"))
        parts.append(block("COMMENT", n, f"C{n}"))
        parts.append(block("ORIGINAL", n, f"O{n}"))
        parts.append(block("JAPANESE", n, f"J{n}"))
        parts.append(block("SPEAKER", n, f"S{n}"))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes("".join(parts).encode("utf-16-le"))


def test_editor_ui_check_files_modifications_comment_save_branch(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / "script_data" / "dr1xml").mkdir(parents=True)

    xml = root / "script_data" / "dr1xml" / "e00_000_000.xml"
    _write_full_xml_two_entries(xml)

    monkeypatch.chdir(root)
    editor_ui.expanduser = lambda p: str(root / "sdse_data_file.json")

    w = editor_ui.Ui_MainWindow()

    called = {"save": 0}
    w.save = lambda: called.__setitem__("save", called["save"] + 1)

    # ret == 3 for translated => go to COMMENT, ret == 1 triggers save() (line ~264)
    w.modification_has_been_made = lambda tag: 3 if tag == "TRANSLATED" else 1

    assert w.check_files_modifications() is True
    assert called["save"] == 1


def test_editor_ui_script_database_changed_and_save_file_pointer_updates(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / "script_data" / "dr1xml").mkdir(parents=True)

    xml = root / "script_data" / "dr1xml" / "e00_000_000.xml"
    _write_full_xml_two_entries(xml)

    monkeypatch.chdir(root)
    editor_ui.expanduser = lambda p: str(root / "sdse_data_file.json")

    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(xml), game="dr1xml", line_index=0)

    # 2 entries -> loop updates pointers (lines ~611-613)
    assert w.script_database_changed("TRANSLATED") is False

    # save_file loop updates pointers (lines ~819-821)
    w.save_file(str(xml), "TRANSLATED")


def test_editor_ui_modification_has_been_made_xml_discard_and_pointer_update(tmp_path: Path, monkeypatch):
    root = tmp_path
    (root / "script_data" / "dr1xml").mkdir(parents=True)

    xml = root / "script_data" / "dr1xml" / "e00_000_000.xml"
    _write_full_xml_two_entries(xml)

    monkeypatch.chdir(root)
    editor_ui.expanduser = lambda p: str(root / "sdse_data_file.json")

    w = editor_ui.Ui_MainWindow()
    w.switch_file(str(xml), game="dr1xml", line_index=0)

    # No unsaved change: should iterate and update pointer positions (lines ~697-699)
    w.plaintexts["TRANSLATED"].setPlainText("T001")
    assert w.modification_has_been_made("TRANSLATED") == 3

    # Force mismatch and take Discard (lines ~690-691)
    w.plaintexts["TRANSLATED"].setPlainText("DIFF")
    monkeypatch.setattr(
        editor_ui.QMessageBox,
        "question",
        staticmethod(lambda *_a, **_kw: editor_ui.QMessageBox.Discard),
    )
    assert w.modification_has_been_made("TRANSLATED") == 0
