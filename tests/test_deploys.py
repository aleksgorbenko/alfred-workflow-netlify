from unittest.mock import patch

from deploys import build_items, main
from netlify_api import NetlifyError


def test_build_items_empty_list_shows_message():
    items = build_items([])
    assert len(items) == 1
    assert items[0]["valid"] is False


def test_build_items_orders_most_recent_first():
    deploys = [
        {
            "id": "old",
            "state": "ready",
            "created_at": "2026-01-01T00:00:00Z",
            "admin_url": "old-url",
        },
        {
            "id": "new",
            "state": "ready",
            "created_at": "2026-06-01T00:00:00Z",
            "admin_url": "new-url",
        },
    ]
    items = build_items(deploys)
    assert [i["arg"] for i in items] == ["new-url/deploys/new", "old-url/deploys/old"]


def test_main_errors_when_token_missing(capsys):
    with patch.dict("os.environ", {}, clear=True):
        main([])
    out = capsys.readouterr().out
    assert "token" in out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"}, clear=True)
def test_main_errors_when_no_site_selected(capsys):
    main([])
    out = capsys.readouterr().out
    assert "no site selected" in out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token", "SITE_ID": "site-1"})
@patch("deploys.netlify_api.list_site_deploys", side_effect=NetlifyError("boom"))
def test_main_surfaces_netlify_error(_mock_list, capsys):
    main([])
    out = capsys.readouterr().out
    assert "boom" in out


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token", "SITE_ID": "site-1"})
@patch(
    "deploys.netlify_api.list_site_deploys",
    return_value=[{"id": "d1", "state": "ready"}],
)
def test_main_emits_deploy_items(_mock_list, capsys):
    main([])
    out = capsys.readouterr().out
    assert "ready" in out
