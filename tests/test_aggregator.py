import pytest

from capsule_brain.tools.aggregator import _safe_eval


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3 * 4", 14),
        ("2 ** 3", 8),
        ("-(5 + 4)", -9),
        ("3.5 + 0.5", 4.0),
    ],
)
def test_safe_eval_valid_expressions(expression: str, expected: float) -> None:
    assert _safe_eval(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "1 and 2",
    ],
)
def test_safe_eval_rejects_unsafe_expressions(expression: str) -> None:
    with pytest.raises(ValueError):
        _safe_eval(expression)
