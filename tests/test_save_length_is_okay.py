from save import length_is_okay


def test_save_length_is_okay_removes_clt_and_checks():
    assert length_is_okay('short') is True
    assert length_is_okay('<CLT 01>hello') is True
    assert length_is_okay('x' * 65) is False
    assert length_is_okay('x' * 10 + '\n' + 'y' * 10) is True
