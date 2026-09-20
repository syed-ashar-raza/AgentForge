from app.agent.agent import Agent

agent = Agent()

tests = [
    "Calculate 25 * 17 + 3.",
    "What is the current UTC date and time?",
    "Say hello and explain that you are AgentForge."
]

for i, goal in enumerate(tests, 1):
    print(f"\n========== LIVE TEST {i} ==========")
    print(f"GOAL: {goal}")

    try:
        result = agent.run(goal)
        print(f"RESULT: {result}")
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
