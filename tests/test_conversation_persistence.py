import uuid
from pathlib import Path


def test_conversation_repo_roundtrip(tmp_path: Path):
    db_path = tmp_path / "test.db"
    from src.db.schema import init_db

    init_db(db_path)
    from src.db.conversations_repo import ConversationsRepository

    repo = ConversationsRepository(db_path)
    conv_id = str(uuid.uuid4())
    conversation = {
        "id": conv_id,
        "agent_id": "dummy_agent",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": "Hello",
                "timestamp": "2024-01-01T00:00:00",
            }
        ],
        "context": {},
        "created_at": "2024-01-01T00:00:00",
        "last_updated": "2024-01-01T00:00:00",
        "status": "active",
    }
    repo.create_conversation(conversation)
    loaded = repo.get_conversation(conv_id)
    assert loaded is not None
    assert loaded["id"] == conv_id
    assert len(loaded["messages"]) == 1
