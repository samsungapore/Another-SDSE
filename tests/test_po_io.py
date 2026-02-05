from pathlib import Path

import pytest

from po_io import PoEntry, parse_context_speaker, read_po, update_po_file, write_po


def test_parse_context_speaker():
    assert parse_context_speaker(None) == (None, None)
    assert parse_context_speaker("") == (None, None)
    assert parse_context_speaker("0001") == ("0001", None)
    assert parse_context_speaker("0001 | MAKOTO") == ("0001", "MAKOTO")
    assert parse_context_speaker(" 0002 |  KYOKO  ") == ("0002", "KYOKO")


def test_read_write_roundtrip(tmp_path: Path):
    p = tmp_path / "x.po"

    entries = [
        PoEntry(
            msgctxt="0001 | MAKOTO",
            msgid="Hello",
            msgstr="Bonjour",
            translator_comments=["note"],
            extracted_comments=["jp line"],
        ),
        PoEntry(
            msgctxt="0002",
            msgid="[EMPTY_LINE]",
            msgstr="[EMPTY_LINE]",
            translator_comments=[],
            extracted_comments=[],
        ),
    ]

    write_po(p, entries)
    got = read_po(p)

    assert len(got) == 2
    assert got[0].msgctxt == "0001 | MAKOTO"
    assert got[0].msgid == "Hello"
    assert got[0].msgstr == "Bonjour"
    assert got[0].translator_comments == ["note"]
    assert got[0].extracted_comments == ["jp line"]

    assert got[1].msgctxt == "0002"
    assert got[1].msgid == "[EMPTY_LINE]"


def test_update_po_file_translated_and_comment(tmp_path: Path):
    p = tmp_path / "y.po"
    write_po(
        p,
        [
            PoEntry(msgctxt="0001 | MAKOTO", msgid="Hello", msgstr=""),
            PoEntry(msgctxt="0002 | KYOKO", msgid="World", msgstr=""),
        ],
    )

    update_po_file(
        p,
        translated=["\nBonjour\n", "\nMonde\n"],
        comment=["\nnote 1\n", "\n\n"],
    )

    got = read_po(p)
    assert [e.msgstr for e in got] == ["Bonjour", "Monde"]
    assert got[0].translator_comments == ["note 1"]
    assert got[1].translator_comments == []
