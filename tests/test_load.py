from ..parser import load
import pytest


@pytest.mark.parametrize("path,expected", [
        ("tests/step1/valid.json", []),
        ("tests/step2/valid.json", ["key", "value"]),
        ("tests/step2/valid2.json", ["key", "value", "key2", "value"]),
])
def test_load(path, expected):
    tokens = load(path)
    assert tokens == expected


@pytest.mark.parametrize("path", [
        "tests/step1/invalid_empty.json",
    ]
)
def test_load_empty(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json" in str(e.value)


@pytest.mark.parametrize("path", [
        "tests/step2/invalid_key.json",
    ]
)
def test_fail_invali_key(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json: expecting quotes" in str(e.value)


@pytest.mark.parametrize("path", [
        "tests/step2/invalid_extra_comma.json",
    ]
)
def test_fail_extra_comma(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json: waiting for new key" in str(e.value)


@pytest.mark.parametrize("path", [
        "tests/step2/invalid_after_end.json",
    ]
)
def test_fail_after_end(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json: expecting no characters after close bracket" in str(e.value)


@pytest.mark.parametrize("path", [
        "tests/step2/invalid_between_tokens.json",
    ]
)
def test_fail_between_tokens(path):
    with pytest.raises(Exception) as e:
        load(path)
    assert "Invalid json: expected comma" in str(e.value)