from pathlib import Path

from script_analyser import XmlAnalyser


def test_xmlanalyser_po_mode(tmp_path: Path):
    root = tmp_path / "script_data" / "dr1"
    root.mkdir(parents=True)

    po = root / "e00_000_000.po"
    po.write_text(
        "\n".join(
            [
                'msgid ""',
                'msgstr ""',
                '"Content-Type: text/plain; charset=UTF-8\\n"',
                '',
                '#. JP1',
                '# note1',
                'msgctxt "0001 | MAKOTO"',
                'msgid "Hello"',
                'msgstr "Bonjour"',
                '',
                'msgctxt "0002"',
                'msgid "[EMPTY_LINE]"',
                'msgstr "[EMPTY_LINE]"',
                '',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    a = XmlAnalyser(str(root))
    assert a.mode == "po"

    for tag in ("ORIGINAL", "TRANSLATED", "COMMENT", "JAPANESE", "SPEAKER"):
        a.analyse_scripts(tag)
        assert str(po) in a.script_data[tag]

    assert a.script_data["ORIGINAL"][str(po)] == ["\nHello\n", "\n\n"]
    assert a.script_data["TRANSLATED"][str(po)] == ["\nBonjour\n", "\n\n"]
    assert a.script_data["COMMENT"][str(po)] == ["\nnote1\n", "\n\n"]
    assert a.script_data["JAPANESE"][str(po)] == ["\nJP1\n", "\n\n"]
    assert a.script_data["SPEAKER"][str(po)] == ["MAKOTO", ""]
