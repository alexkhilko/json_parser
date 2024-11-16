from src.exceptions import InvalidJsonException, InvalidTokenException
from src.parser import load
import pytest


@pytest.mark.parametrize(
    "path,expected",
    [
        ("tests/test_files/valid.json", {}),
        (
            "tests/test_files/valid2.json",
            {
                "key": "value",
                "key2": -344,
                "key3": 588,
                "key4": None,
                "key5": True,
                "key6": False,
            },
        ),
        ("tests/test_files/valid3.json", {"key": "value", "key2": "value"}),
        (
            "tests/test_files/valid_nested.json",
            {"key": "value", "key2": {"key3": "value3", "key4": {"key5": "value5"}}},
        ),
        (
            "tests/test_files/valid_list.json",
            ["foo", "bar", "baz"],
        ),
        (
            "tests/test_files/valid_nested2.json",
            {
                "key": {"key4": ["val4"], "key5": {"key6": ["val6", "val7"]}},
                "key2": ["val1", "val2"],
            },
        ),
        (
            "tests/test_files/valid_nested_3.json",
            {
                "key": "value",
                "key-n": 101,
                "key-o": {"inner key": "inner value"},
                "key-l": ["list value", 10, True, False, None, -20],
            },
        ),
    ],
)
def test_load(path, expected):
    result = load(path)
    assert result == expected


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_empty.json",
    ],
)
def test_load_empty(path):
    with pytest.raises(InvalidJsonException) as e:
        load(path)
    assert "Invalid json" in str(e.value)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_key.json",
    ],
)
def test_fail_invali_key(path):
    with pytest.raises(InvalidJsonException) as e:
        load(path)
    assert "Invalid json: expecting quotes" in str(e.value)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_extra_comma.json",
    ],
)
def test_fail_extra_comma(path):
    with pytest.raises(InvalidJsonException) as e:
        load(path)
    assert "Invalid json: waiting for new key" in str(e.value)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_after_end.json",
    ],
)
def test_fail_after_end(path):
    with pytest.raises(InvalidJsonException) as e:
        load(path)
    assert "Invalid json: expecting no characters after closing bracket" in str(e.value)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_between_tokens.json",
    ],
)
def test_fail_between_tokens(path):
    with pytest.raises(InvalidJsonException) as e:
        load(path)
    assert "Invalid json: expected comma" in str(e.value)


def test_invalid_close_bracket():
    with pytest.raises(InvalidJsonException) as e:
        load("tests/test_files/invalid_close_bracket.json")
    assert "Invalid json: Invalid character } before start" in str(e.value)


@pytest.mark.parametrize(
    "path, error_token",
    [
        ("tests/test_files/invalid_false.json", "Fa"),
        ("tests/test_files/invalid_true.json", "truet"),
        ("tests/test_files/invalid_null.json", "nul"),
        ("tests/test_files/invalid_nested_3.json", "'l"),

    ],
)
def test_invalid_mix_tokens(path, error_token):
    with pytest.raises(InvalidTokenException) as e:
        load(path)
    assert e.value.invalid_token == error_token
