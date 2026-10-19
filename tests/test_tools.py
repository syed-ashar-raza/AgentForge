from app.tools.builtin import calculator


def test_calculator() -> None:
    assert calculator("2 + 3 * 4") == "14"


def test_calculator_rejects_code() -> None:
    try:
        calculator("__import__('os').system('whoami')")
    except ValueError:
        return
    raise AssertionError("Unsafe calculator input was accepted")


def test_calculator_rejects_non_finite_results() -> None:
    import pytest

    with pytest.raises(ValueError):
        calculator("1e308 * 1e308")


def test_tool_rejects_non_dictionary_arguments() -> None:
    import pytest

    from app.tools.builtin import Tool

    tool = Tool(
        name="safe_test",
        description="Test argument validation",
        function=lambda **kwargs: kwargs,
    )

    with pytest.raises(ValueError, match="arguments must be a dictionary"):
        tool.execute(["unexpected"])
