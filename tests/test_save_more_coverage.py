from save import get_key, length_is_okay


def _idx(buf: str) -> int:
    return buf.find('<TRANSLATED N°') + len('<TRANSLATED N°')


def test_get_key_long_branches():
    # last digit != 0
    buf = '<TRANSLATED N°009>\nX\n</TRANSLATED N°009>'
    assert get_key(buf, _idx(buf), long=True).endswith('.txt')

    # nested zeros (hits deeper branches)
    buf2 = '<TRANSLATED N°1000>\nX\n</TRANSLATED N°1000>'
    out = get_key(buf2, _idx(buf2), long=True)
    assert out.startswith('0')
    assert out.endswith('.txt')

    # cover script_nb[-3] != '0' branch (line ~24)
    buf3 = '<TRANSLATED N°1100>\nX\n</TRANSLATED N°1100>'
    out3 = get_key(buf3, _idx(buf3), long=True)
    assert out3.endswith('.txt')


def test_length_is_okay_multiline_long_first_line():
    s = ('x' * 65) + '\nshort'
    assert length_is_okay(s) is False
