from unittest.mock import patch

from envvars import build_items, main
from netlify_api import NetlifyError


def test_build_items_empty_list_shows_message():
    items = build_items([])
    assert len(items) == 1
    assert items[0]["valid"] is False


def test_build_items_sorts_by_key():
    env_vars = [{"key": "ZETA", "values": []}, {"key": "ALPHA", "values": []}]
    items = build_items(env_vars)
    assert [i["title"] for i in items] == ["ALPHA", "ZETA"]


def test_main_errors_when_site_or_account_missing(capsys):
    with patch.dict("os.environ", {"NETLIFY_TOKEN": "token"}, clear=True):
        main([])
    out = capsys.readouterr().out
    assert "no site selected" in out.lower()


@patch.dict(
    "os.environ", {"NETLIFY_TOKEN": "token", "SITE_ID": "site-1", "ACCOUNT_ID": "acc-1"}
)
@patch("envvars.netlify_api.get_env_vars", side_effect=NetlifyError("boom"))
def test_main_surfaces_netlify_error(_mock_get, capsys):
    main([])
    out = capsys.readouterr().out
    assert "boom" in out


@patch.dict(
    "os.environ", {"NETLIFY_TOKEN": "token", "SITE_ID": "site-1", "ACCOUNT_ID": "acc-1"}
)
@patch("envvars.netlify_api.get_env_vars", return_value=[{"key": "FOO", "values": []}])
def test_main_emits_envvar_items(_mock_get, capsys):
    main([])
    out = capsys.readouterr().out
    assert "FOO" in out
