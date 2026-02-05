from pathlib import Path

from json_file_working import append_dump_into_json, dump_into_json, load_json_file
from save import get_key, right_key


def test_json_helpers(tmp_path: Path):
    p = tmp_path / "x.json"
    assert load_json_file(str(p)) == {}

    # missing file append
    assert append_dump_into_json(str(tmp_path / "missing.json"), {"x": 1}) is False

    dump_into_json(str(p), {"a": 1})
    assert load_json_file(str(p)) == {"a": 1}

    assert append_dump_into_json(str(p), {"b": 2}) is None or append_dump_into_json(str(p), {"b": 2}) is True
    data = load_json_file(str(p))
    assert data["a"] == 1
    assert data["b"] == 2


def test_get_key_and_right_key():
    # Minimal fake buffer containing a tag like <TRANSLATED N°001>
    buf = "<TRANSLATED N°001>\nX\n</TRANSLATED N°001>"
    idx = buf.find("<TRANSLATED N°") + len("<TRANSLATED N°")

    assert get_key(buf, idx) == "001"
    assert right_key("001", buf, idx) is True
    assert right_key("999", buf, idx) is False

    # cover long=True branches
    buf2 = "<TRANSLATED N°010>\nX\n</TRANSLATED N°010>"
    idx2 = buf2.find("<TRANSLATED N°") + len("<TRANSLATED N°")
    assert get_key(buf2, idx2, long=True).endswith('.txt')
