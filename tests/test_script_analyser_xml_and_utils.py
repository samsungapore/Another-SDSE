from pathlib import Path

from script_analyser import (
    XmlAnalyser,
    cleaned_text,
    find_to_remove,
    get_file_script,
    length_is_okay,
    open_file,
)


def test_cleaned_text_and_len():
    line = "abc<CLT 01>def<CLT>ghi"
    assert cleaned_text(line) == "abcdefghi"
    assert find_to_remove(line) > 0

    assert length_is_okay("short") is True
    assert length_is_okay("x" * 65) is False
    assert length_is_okay("x" * 64) is True
    assert length_is_okay("x" * 40 + "\n" + "x" * 40) is True


def test_get_file_script_basic():
    buf = (
        "<TRANSLATED N°001>\nBonjour\n</TRANSLATED N°001>\n"
        "<TRANSLATED N°002>\n\n</TRANSLATED N°002>\n"
    )
    lines = get_file_script(buf, tag_name="TRANSLATED")
    assert lines == ["\nBonjour\n", "\n\n"]


def test_xmlanalyser_xml_mode(tmp_path: Path):
    root = tmp_path / "script_data" / "dr1"
    root.mkdir(parents=True)

    # DRAT-style XML is actually UTF-16LE.
    xml = root / "e00_000_000.xml"
    xml_content = (
        "<ORIGINAL N°001>\nHello\n</ORIGINAL N°001>\n"
        "<TRANSLATED N°001>\nBonjour\n</TRANSLATED N°001>\n"
        "<COMMENT N°001>\nnote\n</COMMENT N°001>\n"
    )
    xml.write_bytes(xml_content.encode("utf-16-le"))

    a = XmlAnalyser(str(root))
    assert a.mode == "xml"

    a.analyse_scripts("ORIGINAL")
    assert str(xml) in a.script_data["ORIGINAL"]
    assert a.script_data["ORIGINAL"][str(xml)] == ["\nHello\n"]

    # open_file should decode it
    decoded = open_file(str(xml))
    assert "Hello" in decoded
