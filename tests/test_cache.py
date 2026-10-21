from typing import TYPE_CHECKING

from cache import PRIVATE_DIRECTORY, cached

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

PRIVATE_FILE = 0o600
ONE_HOUR = 3600
FALLBACK_VALUE = 3


def test_cached_value_is_written_privately(tmp_path: Path) -> None:
    tmp_path.chmod(0o755)
    assert cached("k", ONE_HOUR, lambda: {"a": 1}) == {"a": 1}
    written = next(tmp_path.glob("*.json"))
    assert written.stat().st_mode & 0o777 == PRIVATE_FILE
    assert tmp_path.stat().st_mode & 0o777 == PRIVATE_DIRECTORY


def test_fresh_value_is_read_from_disk() -> None:
    cached("k", ONE_HOUR, lambda: [1])
    assert cached("k", ONE_HOUR, lambda: [2]) == [1]


def test_missing_cache_folder_falls_back_to_temp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("alfred_workflow_cache")
    assert cached("fallback", 0, lambda: FALLBACK_VALUE) == FALLBACK_VALUE
