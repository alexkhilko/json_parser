from ..parser import load
import pytest


@pytest.mark.parametrize(
    "path,expected",
    [
        ("tests/test_files/valid.json", {}),
        ("tests/test_files/valid2.json", {"key": "value", "key2": -344, "key3": 588}),
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
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json" in str(e.value)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_key.json",
    ],
)
def test_fail_invali_key(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json: expecting quotes" in str(e.value)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_extra_comma.json",
    ],
)
def test_fail_extra_comma(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json: waiting for new key" in str(e.value)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_after_end.json",
    ],
)
def test_fail_after_end(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json: expecting no characters after close bracket" in str(e.value)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_files/invalid_between_tokens.json",
    ],
)
def test_fail_between_tokens(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json: expected comma" in str(e.value)


def test_invalid_close_bracket():
    with pytest.raises(Exception) as e:
        load("tests/test_files/invalid_close_bracket.json")
    assert "Invalid json: Invalid character } before start" in str(e.value)
