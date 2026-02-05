from types import SimpleNamespace

from script_analyser import cleaned_text, count_rem, find_to_remove, find_w_line


def test_find_w_line_and_count_rem_edges():
    block = ["a", "b"]

    # Cursor positions that don't match exactly should fall back to last line.
    cur = SimpleNamespace(position=lambda: 999)
    assert find_w_line(cur, block) == "b"

    # count_rem: no '>'
    rem, nxt = count_rem("<abc", 0)
    assert rem >= 0
    assert nxt > 0

    s = "<A>xx</A>"
    assert find_to_remove(s) > 0
    assert cleaned_text("<X>hello</X>") == "hello"
