from datetime import UTC, datetime, timedelta

from alfred_items import deploy_state, deploy_title, item, notice, relative_time


def _ago(**delta: float) -> str:
    return (datetime.now(UTC) - timedelta(**delta)).isoformat()


def test_item_omits_optional_keys() -> None:
    assert item("Title") == {"title": "Title", "subtitle": "", "valid": True}


def test_notice_is_invalid() -> None:
    assert notice("Oops")["valid"] is False


def test_relative_time_buckets() -> None:
    assert relative_time(_ago(seconds=5)) == "just now"
    assert relative_time(_ago(minutes=5)) == "5m ago"
    assert relative_time(_ago(hours=3)) == "3h ago"
    assert relative_time(_ago(days=2)) == "2d ago"


def test_deploy_state_shows_error_message() -> None:
    deploy = {"state": "error", "error_message": "Build failed"}
    assert deploy_state(deploy) == "🔴 error - Build failed"


def test_deploy_state_marks_active_and_unknown() -> None:
    assert deploy_state({"state": "building"}) == "🟡 building"
    assert deploy_state({"state": "skipped"}) == "⚪ skipped"


def test_deploy_title_joins_context_and_branch() -> None:
    assert deploy_title({"id": "d1", "context": "production", "branch": "main"}) == (
        "production / main"
    )
    assert deploy_title({"id": "d1"}) == "d1"
