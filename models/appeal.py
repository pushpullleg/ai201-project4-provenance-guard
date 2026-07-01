from models.audit import get_entry, update_appeal as _db_update_appeal, get_log


def submit_appeal(content_id: str, reasoning: str) -> dict:
    """
    Submit an appeal for a classified content entry.

    Raises ValueError if content_id not found.
    Raises RuntimeError if DB update fails.
    Returns confirmation dict on success.
    """
    entry = get_entry(content_id)
    if not entry:
        raise ValueError(f"content_id '{content_id}' not found")

    success = _db_update_appeal(content_id, reasoning)
    if not success:
        raise RuntimeError(f"Failed to update appeal for '{content_id}'")

    return {
        "message": "Appeal received. Your content is now under review.",
        "content_id": content_id,
        "status": "under_review",
    }


def get_appeals() -> list:
    """Return all log entries with status 'under_review'."""
    return [e for e in get_log(limit=1000) if e.get("status") == "under_review"]
