from pathlib import Path

import pytest

from po_io import PoEntry, read_po, write_po


def test_read_po_invalid_string_literal(tmp_path: Path):
    p = tmp_path / 'bad.po'
    p.write_text('msgid ""\nmsgstr ""\n\nmsgid not_a_string\n', encoding='utf-8')

    # Parsing should not crash hard; it will ignore unknown lines and then flush header only.
    # Here we include a bad msgid value which should raise.
    p.write_text('msgid ""\nmsgstr ""\n\nmsgid not_a_string\nmsgstr "x"\n', encoding='utf-8')
    with pytest.raises(ValueError):
        read_po(p)


def test_read_po_missing_msgid_raises(tmp_path: Path):
    p = tmp_path / 'bad2.po'
    p.write_text('msgstr "x"\n', encoding='utf-8')
    with pytest.raises(ValueError):
        read_po(p)


def test_write_po_handles_empty_comments(tmp_path: Path):
    p = tmp_path / 'z.po'
    write_po(p, [PoEntry(msgctxt=None, msgid='A', msgstr='B', translator_comments=[''], extracted_comments=[''])])
    txt = p.read_text('utf-8')
    assert '#.' in txt
    assert '#\n' in txt or '# \n' in txt
