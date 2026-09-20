from app.memory.store import MemoryStore


def test_memory_round_trip(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.db", limit=3)

    store.add("user", "hello")
    store.add("assistant", "hi")

    messages = store.recent()

    assert messages == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
