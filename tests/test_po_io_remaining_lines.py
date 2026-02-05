from pathlib import Path

from po_io import read_po


def test_po_trailing_backslash_and_no_header(tmp_path: Path):
    # trailing backslash escape path
    p = tmp_path / 't.po'
    p.write_text(
        '\n'.join(
            [
                'msgctxt "0001"',
                'msgid "Hello\\"',
                'msgstr ""',
                '',
            ]
        )
        + '\n',
        encoding='utf-8',
    )

    e = read_po(p)
    assert e[0].msgid.endswith('\\')


def test_po_missing_msgstr_defaults_to_empty_and_unknown_lines_ignored(tmp_path: Path):
    p = tmp_path / 'm.po'
    p.write_text(
        '\n'.join(
            [
                'msgctxt "0001"',
                'msgid "Hello"',
                'this is an unknown line that should be ignored',
                '',
            ]
        )
        + '\n',
        encoding='utf-8',
    )

    e = read_po(p)
    assert len(e) == 1
    assert e[0].msgid == 'Hello'
    assert e[0].msgstr == ''
