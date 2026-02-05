from pathlib import Path

from script_analyser import SDSE1_Analyser


def test_sdse1_analyser_reacts_and_data(tmp_path: Path, capsys):
    root = tmp_path / 'umd'
    root.mkdir()

    # Create a fake "e00.lin" directory.
    lindir = root / 'e00.lin'
    pakdir = lindir / 'e00.pak'
    pakdir.mkdir(parents=True)

    # One react file with CLT 1 marker
    (pakdir / 'a.txt').write_text('hello CLT 1>AAA<CLT> world', encoding='utf-8')

    # One normal file (utf-16-le) without marker
    (pakdir / 'b.txt').write_bytes('bonjour'.encode('utf-16-le'))

    a = SDSE1_Analyser(str(root))
    a.analyse_scripts()

    # Should have at least one react and one data entry
    assert len(a.reacts) == 1
    assert len(a.data) == 1

    # Capture output printing missing react links (should print e00.lin/a.txt or nothing)
    _ = capsys.readouterr()
