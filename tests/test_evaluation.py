import pytest

from app.evaluation.run import score_decisions


def make_case(action="tool", tool="calculator"):
    return {
        "request": "Calculate 2 + 3",
        "expected_action": action,
        "expected_tool": tool,
    }


def make_decision(action="tool", tool="calculator"):
    return {"action": action, "tool_name": tool}


def test_perfect_scores_return_full_accuracy():
    result = score_decisions(
        [make_case(), make_case(action="final", tool=None)],
        [
            make_decision(),
            make_decision(action="final", tool=None),
        ],
    )

    assert result["total_cases"] == 2
    assert result["decision_accuracy"] == 1.0
    assert result["tool_selection_accuracy"] == 1.0
    assert result["failures"] == []


def test_incorrect_decision_is_reported():
    result = score_decisions(
        [make_case()],
        [make_decision(action="final", tool=None)],
    )

    assert result["decision_accuracy"] == 0.0
    assert result["tool_selection_accuracy"] == 0.0
    assert len(result["failures"]) == 1
    assert result["failures"][0]["case"] == 1


def test_empty_dataset_is_rejected():
    with pytest.raises(RuntimeError, match="dataset is empty"):
        score_decisions([], [])


def test_mismatched_case_and_decision_counts_are_rejected():
    with pytest.raises(ValueError, match="equal lengths"):
        score_decisions([make_case()], [])
