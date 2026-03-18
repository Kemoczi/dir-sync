import pytest
from sync_dirs import natural_int, parse_interval
from argparse import ArgumentTypeError

NINT_OK = [(1,1), (1.5, 1)] # type: ignore
NINT_ERR = (0, "dd", "20.5", "1,5", "0", "-1", -1.1)

INTERVAL_OK = [(10, 10), ("01:20:10", 4810), ("1:2:3", 3723)]
INTERVAL_ERR = ("dd", 11.5, "10::1")



@pytest.mark.parametrize("value, result", NINT_OK) # type: ignore
def test_natural_int(value: int, result: int):
    assert natural_int(value) == result


@pytest.mark.parametrize("value", NINT_ERR)
def test_natural_int_arg_error(value: str):
    with pytest.raises(ArgumentTypeError):
        natural_int(value)

@pytest.mark.parametrize("input, result", INTERVAL_OK)
def test_parse_interval(input: str, result: int):
    assert parse_interval(input) == result

@pytest.mark.parametrize("input", INTERVAL_ERR)
def test_parse_interval_arg_error(input: str):
    with pytest.raises(ArgumentTypeError):
        parse_interval(input)
