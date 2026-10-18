import json
from pathlib import Path

from app.llm.client import OllamaClient
from app.tools.registry import ToolRegistry


def score_decisions(
    cases: list[dict[str, object]],
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    if not cases:
        raise RuntimeError("Evaluation dataset is empty.")

    if len(cases) != len(decisions):
        raise ValueError("Cases and decisions must have equal lengths.")

    correct_actions = 0
    correct_tools = 0
    failures: list[dict[str, object]] = []
    categories: dict[str, dict[str, int]] = {}

    for index, (case, decision) in enumerate(
        zip(cases, decisions, strict=True), start=1
    ):
        expected_action = case["expected_action"]
        expected_tool = case["expected_tool"]
        actual_action = decision["action"]
        actual_tool = decision["tool_name"]

        action_correct = actual_action == expected_action
        tool_correct = actual_tool == expected_tool
        correct_actions += action_correct
        correct_tools += tool_correct

        category = str(expected_tool or "no_tool")
        metrics = categories.setdefault(
            category, {"total": 0, "correct_actions": 0, "correct_tools": 0}
        )
        metrics["total"] += 1
        metrics["correct_actions"] += action_correct
        metrics["correct_tools"] += tool_correct

        if not action_correct or not tool_correct:
            failures.append(
                {
                    "case": index,
                    "request": case["request"],
                    "expected_action": expected_action,
                    "actual_action": actual_action,
                    "expected_tool": expected_tool,
                    "actual_tool": actual_tool,
                }
            )

    total = len(cases)
    category_metrics = {
        name: {
            "total_cases": metrics["total"],
            "decision_accuracy": round(
                metrics["correct_actions"] / metrics["total"], 4
            ),
            "tool_selection_accuracy": round(
                metrics["correct_tools"] / metrics["total"], 4
            ),
        }
        for name, metrics in sorted(categories.items())
    }

    return {
        "total_cases": total,
        "decision_accuracy": round(correct_actions / total, 4),
        "tool_selection_accuracy": round(correct_tools / total, 4),
        "category_metrics": category_metrics,
        "failures": failures,
    }


def main() -> None:
    dataset_path = Path("evals/decision_cases.jsonl")
    cases = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]

    client = OllamaClient()
    tools = ToolRegistry().list_tools()
    decisions = [
        client.decide_tool(case["request"], tools)
        for case in cases
    ]

    report = {
        "model": client.model,
        **score_decisions(cases, decisions),
    }

    report_path = Path("evals/latest_report.json")
    report_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()
