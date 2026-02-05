from __future__ import annotations

from pathlib import Path

import pytest

import script_analyser
from script_analyser import SDSE1_Analyser, XmlAnalyser, length_is_okay, right_len


def _write_bin(path: Path, text: str, *, encoding: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode(encoding))


def _write_xml_two_entries(path: Path):
    # Two entries so loops update begin/end pointers.
    # Keep TRANSLATED[001] exactly "\n\n" for the check_line_length branch.
    # Make ORIGINAL[001] a single long line (>64) with no leading newline so right_len() returns False.
    xml = (
        "<TRANSLATED N°001>\n\n</TRANSLATED N°001>\n"
        + "<ORIGINAL N°001>" + ("x" * 65) + "</ORIGINAL N°001>\n"
        + "<TRANSLATED N°002>\nOK\n</TRANSLATED N°002>\n"
        + "<ORIGINAL N°002>\nORIG\n</ORIGINAL N°002>\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(xml.encode("utf-16-le"))


def _write_po(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
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
        encoding="utf-8",
    )


def test_length_is_okay_multiline_long_returns_false():
    assert length_is_okay(("x" * 65) + "\nshort") is False


def test_right_len_single_and_multiline_false_branches():
    assert right_len("x" * 65) is False
    assert right_len(("x" * 65) + "\nshort") is False


def _setup_sdse1_tree(tmp_path: Path, *, data_text: str) -> Path:
    root = tmp_path

    # non-.lin entry (covers continue)
    (root / "not_a_lin.txt").write_text("x")

    # a .lin without .pak (covers continue)
    (root / "missing.lin").mkdir()

    # a .lin with .pak containing two files
    pak = root / "e00.lin" / "e00.pak"
    pak.mkdir(parents=True)

    # file that goes to reacts (contains CLT 1).
    # Prefix with invalid UTF-8 bytes so the code hits the UnicodeDecodeError fallback.
    raw = b"\xff\xff" + "<CLT 1>MAGIC<CLT>".encode("utf-16-le")
    (pak / "a.txt").write_bytes(raw)

    # file that goes to data
    _write_bin(pak / "b.txt", data_text, encoding="utf-8")

    return root


def test_sdse1_analyser_analyse_scripts_prints_when_not_found(tmp_path: Path, capsys):
    root = _setup_sdse1_tree(tmp_path, data_text="plain data only")

    a = SDSE1_Analyser(str(root))
    a.analyse_scripts()

    out = capsys.readouterr().out
    assert "e00.lin/a.txt" in out


def test_sdse1_analyser_analyse_scripts_ok_true_branch(tmp_path: Path, capsys):
    root = _setup_sdse1_tree(tmp_path, data_text="contains MAGIC here")

    a = SDSE1_Analyser(str(root))
    a.analyse_scripts()

    out = capsys.readouterr().out
    assert out == ""


def test_xml_analyser_xml_filenotfound_continues(tmp_path: Path, monkeypatch):
    root = tmp_path / "xml"
    (root / "x").mkdir(parents=True)
    (root / "x" / "x.xml").write_text("<TRANSLATED N°001>\nX\n</TRANSLATED N°001>")

    xa = XmlAnalyser(str(root))
    assert xa.mode == "xml"

    monkeypatch.setattr(script_analyser, "open_file", lambda *_a, **_kw: (_ for _ in ()).throw(FileNotFoundError()))
    xa.analyse_scripts("TRANSLATED")
    assert xa.script_data["TRANSLATED"] == {}


def test_xml_analyser_po_mode_skips_non_po_and_unknown_tag(tmp_path: Path):
    root = tmp_path / "po"
    _write_po(root / "a.po")
    (root / "readme.txt").write_text("hi")

    xa = XmlAnalyser(str(root))
    assert xa.mode == "po"

    xa.analyse_scripts("BLAH")
    assert list(xa.script_data["BLAH"].values())[0] == ["\n\n"]


def test_xml_analyser_check_line_length_and_show_script_data(tmp_path: Path, capsys):
    root = tmp_path / "xml2"
    # Expected structure: xml_path/<dir>/<dir>.xml
    _write_xml_two_entries(root / "dir1" / "dir1.xml")

    xa = XmlAnalyser(str(root))
    xa.check_line_length()

    out = capsys.readouterr().out
    assert "\n\n" in out  # printed empty translated when original too long

    # show_script_data else branch (tag != TRANSLATED)
    xa.analyse_scripts("ORIGINAL")
    xa.show_script_data("ORIGINAL")
