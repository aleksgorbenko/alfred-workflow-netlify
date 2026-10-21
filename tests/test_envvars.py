from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from envvars import build_items, main
from netlify_api import NetlifyError

if TYPE_CHECKING:
    import pytest


def test_build_items_empty_list_shows_message() -> None:
    items = build_items([])
    assert len(items) == 1
    assert items[0]["valid"] is False


def test_build_items_sorts_by_key() -> None:
    env_vars: list[dict[str, Any]] = [
        {"key": "ZETA", "values": []},
        {"key": "ALPHA", "values": []},
    ]
    items = build_items(env_vars)
    assert [i["title"] for i in items] == ["ALPHA", "ZETA"]


def test_main_errors_when_site_or_account_missing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with patch.dict("os.environ", {"NETLIFY_TOKEN": "token"}, clear=True):
        main([])
    out = capsys.readouterr().out
    assert "no site selected" in out.lower()


@patch.dict(
    "os.environ", {"NETLIFY_TOKEN": "token", "SITE_ID": "site-1", "ACCOUNT_ID": "acc-1"}
)
@patch("envvars.netlify_api.get_env_vars", side_effect=NetlifyError("boom"))
def test_main_surfaces_netlify_error(
    mock_get: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    main([])
    mock_get.assert_called_once()
    out = capsys.readouterr().out
    assert "boom" in out


@patch.dict(
    "os.environ", {"NETLIFY_TOKEN": "token", "SITE_ID": "site-1", "ACCOUNT_ID": "acc-1"}
)
@patch("envvars.netlify_api.get_env_vars", return_value=[{"key": "FOO", "values": []}])
def test_main_emits_envvar_items(
    mock_get: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    main([])
    mock_get.assert_called_once()
    out = capsys.readouterr().out
    assert "FOO" in out
