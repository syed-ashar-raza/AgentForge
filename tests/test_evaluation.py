import pytest

from app.evaluation.run import evaluate_decisions, score_decisions


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


def test_category_metrics_separate_tool_types():
    cases = [
        make_case(tool="calculator"),
        make_case(tool="current_datetime"),
        make_case(action="final", tool=None),
    ]
    decisions = [
        make_decision(),
        make_decision(action="tool", tool="calculator"),
        make_decision(action="final", tool=None),
    ]

    result = score_decisions(cases, decisions)
    categories = result["category_metrics"]

    assert categories["calculator"]["decision_accuracy"] == 1.0
    assert categories["current_datetime"]["decision_accuracy"] == 1.0
    assert categories["current_datetime"]["tool_selection_accuracy"] == 0.0
    assert categories["no_tool"]["decision_accuracy"] == 1.0
    assert categories["no_tool"]["total_cases"] == 1


def test_category_metrics_handle_multiple_cases():
    cases = [make_case(), make_case()]
    decisions = [
        make_decision(),
        make_decision(action="final", tool=None),
    ]

    result = score_decisions(cases, decisions)

    assert result["category_metrics"]["calculator"]["total_cases"] == 2
    assert result["category_metrics"]["calculator"]["decision_accuracy"] == 0.5



def test_evaluate_decisions_records_inference_failures():
    class MockClient:
        def decide_tool(self, request, tools):
            if request == "fail":
                raise RuntimeError("Ollama unavailable")
            return {"action": "tool", "tool_name": "calculator"}

    cases = [
        {"request": "Calculate 2 + 3"},
        {"request": "fail"},
    ]

    decisions, inference_failures = evaluate_decisions(
        cases, MockClient(), []
    )

    assert len(decisions) == 2
    assert decisions[0]["action"] == "tool"
    assert decisions[1]["action"] == "error"
    assert len(inference_failures) == 1
    assert inference_failures[0]["case"] == 2
    assert "Ollama unavailable" in inference_failures[0]["error"]


def test_evaluate_decisions_returns_no_failures_on_success():
    class MockClient:
        def decide_tool(self, request, tools):
            return {"action": "final", "tool_name": None}

    decisions, inference_failures = evaluate_decisions(
        [{"request": "Hello"}], MockClient(), []
    )

    assert decisions == [{"action": "final", "tool_name": None}]
    assert inference_failures == []
