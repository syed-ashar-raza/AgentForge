import json
from pathlib import Path

from app.llm.client import OllamaClient
from app.tools.registry import ToolRegistry


def main() -> None:
    dataset_path = Path("evals/decision_cases.jsonl")
    cases = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]

    client = OllamaClient()
    tools = ToolRegistry().list_tools()
    correct_actions = 0
    correct_tools = 0
    failures: list[dict[str, object]] = []

    for index, case in enumerate(cases, start=1):
        decision = client.decide_tool(case["request"], tools)
        action_correct = decision["action"] == case["expected_action"]
        tool_correct = decision["tool_name"] == case["expected_tool"]
        correct_actions += action_correct
        correct_tools += tool_correct

        if not action_correct or not tool_correct:
            failures.append(
                {
                    "case": index,
                    "request": case["request"],
                    "expected_action": case["expected_action"],
                    "actual_action": decision["action"],
                    "expected_tool": case["expected_tool"],
                    "actual_tool": decision["tool_name"],
                }
            )

    total = len(cases)
    if total == 0:
        raise RuntimeError("Evaluation dataset is empty.")

    report = {
        "model": client.model,
        "total_cases": total,
        "decision_accuracy": round(correct_actions / total, 4),
        "tool_selection_accuracy": round(correct_tools / total, 4),
        "failures": failures,
    }

    report_path = Path("evals/latest_report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()
