from pathlib import Path

import pytest

from po_io import PoEntry, read_po, update_po_file, write_po


def test_po_unquote_escapes_and_unknown_escape(tmp_path: Path):
    p = tmp_path / 'e.po'
    p.write_text(
        "\n".join(
            [
                'msgid ""',
                'msgstr ""',
                '"Content-Type: text/plain; charset=UTF-8\\n"',
                '',
                'msgctxt "0001"',
                'msgid "Hello\\nWorld\\t\\r\\\\\\\"X\\q"',
                'msgstr "Bonjour"',
                '',
            ]
        )
        + "\n",
        encoding='utf-8',
    )

    entries = read_po(p)
    assert len(entries) == 1
    assert 'Hello' in entries[0].msgid
    assert 'World' in entries[0].msgid
    assert '"' in entries[0].msgid
    # unknown escape \q keeps literal 'q'
    assert entries[0].msgid.endswith('Xq')


def test_po_multiline_and_missing_value(tmp_path: Path):
    p = tmp_path / 'm.po'
    p.write_text(
        "\n".join(
            [
                'msgid ""',
                'msgstr ""',
                '',
                'msgid "a"',
                '"b"',
                'msgstr "c"',
                '',
            ]
        )
        + "\n",
        encoding='utf-8',
    )
    e = read_po(p)
    assert e[0].msgid == 'ab'

    p2 = tmp_path / 'bad.po'
    p2.write_text('msgid ""\nmsgstr ""\n\nmsgid\nmsgstr "x"\n', encoding='utf-8')
    with pytest.raises(ValueError):
        read_po(p2)


def test_update_po_file_mismatch_raises(tmp_path: Path):
    p = tmp_path / 'u.po'
    write_po(p, [PoEntry(msgctxt='0001', msgid='A', msgstr='')])

    with pytest.raises(ValueError):
        update_po_file(p, translated=['\nx\n', '\ny\n'])

    with pytest.raises(ValueError):
        update_po_file(p, comment=['\nx\n', '\ny\n'])
