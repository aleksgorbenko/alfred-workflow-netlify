from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from netlify_api import NetlifyError
from sites import build_items, main

if TYPE_CHECKING:
    import pytest


def test_build_items_empty_list_shows_message() -> None:
    items = build_items([], "")
    assert len(items) == 1
    assert items[0]["valid"] is False


def test_build_items_filters_by_query() -> None:
    sites = [{"id": "1", "name": "blog"}, {"id": "2", "name": "docs-site"}]
    items = build_items(sites, "blog")
    assert len(items) == 1
    assert items[0]["title"] == "blog"


def test_build_items_no_query_returns_all_sorted() -> None:
    sites = [{"id": "1", "name": "zeta"}, {"id": "2", "name": "alpha"}]
    items = build_items(sites, "")
    assert [i["title"] for i in items] == ["alpha", "zeta"]


def test_build_items_no_matches_shows_query_in_message() -> None:
    items = build_items([{"id": "1", "name": "blog"}], "nonexistent")
    assert "nonexistent" in items[0]["title"]


def test_main_errors_when_token_missing(capsys: pytest.CaptureFixture[str]) -> None:
    with patch.dict("os.environ", {}, clear=True):
        main([""])
    out = capsys.readouterr().out
    assert "token" in out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"})
@patch("sites.netlify_api.list_sites", side_effect=NetlifyError("boom"))
def test_main_surfaces_netlify_error(
    mock_list: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    main([""])
    mock_list.assert_called_once()
    out = capsys.readouterr().out
    assert "boom" in out


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"})
@patch("sites.netlify_api.list_sites", return_value=[{"id": "1", "name": "blog"}])
def test_main_emits_site_items(
    mock_list: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    main([""])
    mock_list.assert_called_once()
    out = capsys.readouterr().out
    assert "blog" in out
