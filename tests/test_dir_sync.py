import pytest
import sync_dirs
import shutil
from argparse import ArgumentTypeError

NINT_OK = [(1,1), (1.5, 1)]
NINT_ERR = (0, "dd", "20.5", "1,5", "0", "-1", -1.1)

INTERVAL_OK = [(10, 10), ("01:20:10", 4810), ("1:2:3", 3723)]
INTERVAL_ERR = ("dd", 11.5, "10::1")


@pytest.mark.unit
@pytest.mark.parametrize("value, result", NINT_OK)
def test_natural_int(value: int, result: int):
    assert sync_dirs.natural_int(value) == result


@pytest.mark.unit
@pytest.mark.parametrize("value", NINT_ERR)
def test_natural_int_arg_error(value: str):
    with pytest.raises(ArgumentTypeError):
        sync_dirs.natural_int(value)


@pytest.mark.unit
@pytest.mark.parametrize("input, result", INTERVAL_OK)
def test_parse_interval(input: str, result: int):
    assert sync_dirs.parse_interval(input) == result


@pytest.mark.unit
@pytest.mark.parametrize("input", INTERVAL_ERR)
def test_parse_interval_arg_error(input: str):
    with pytest.raises(ArgumentTypeError):
        sync_dirs.parse_interval(input)

########## INTEGRATION TESTS ################

def test_sync_copies_new_file(tmp_path):
    source = tmp_path / "source"
    replica = tmp_path / "replica"
    source.mkdir(exist_ok=True)

    (source / "file.txt").write_text("Lorem ipsum", encoding="utf-8")

    sync_dirs.sync(source, replica)

    assert (replica / "file.txt").exists()
    assert (replica / "file.txt").read_text(encoding="utf-8") == "Lorem ipsum"


def test_sync_copy_permission_error(tmp_path, monkeypatch, caplog):
    source = tmp_path / "source"
    replica = tmp_path / "replica"
    source.mkdir()
    replica.mkdir()

    file_path = source / "file.txt"
    file_path.write_text("hello", encoding="utf-8")

    def fake_copy2(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(shutil, "copy2", fake_copy2)

    sync_dirs.copy_items(source, replica, excluded=set())

    assert "Problem with copying file" in caplog.text
    assert "denied" in caplog.text
