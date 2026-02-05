from pathlib import Path

from script_analyser import XmlAnalyser, right_len


def test_right_len_multiline_behavior():
    assert right_len('x' * 10) is True
    # multi-line: function returns after first line in current implementation
    assert right_len('x' * 10 + '\n' + ('y' * 100)) is True


def test_check_line_length_and_show_script_data(tmp_path: Path, capsys):
    root = tmp_path / 'xmlroot'
    root.mkdir()

    d = root / 'e00_000_000'
    d.mkdir()
    xml = d / 'e00_000_000.xml'
    xml.write_bytes(
        (
            '<ORIGINAL N°001>\nHello\n</ORIGINAL N°001>\n'
            '<TRANSLATED N°001>\nBonjour\n</TRANSLATED N°001>\n'
        ).encode('utf-16-le')
    )

    a = XmlAnalyser(str(root))
    a.analyse_scripts('TRANSLATED')
    a.check_line_length()

    a.show_script_data('TRANSLATED')
    out = capsys.readouterr().out
    assert 'Bonjour' in out
