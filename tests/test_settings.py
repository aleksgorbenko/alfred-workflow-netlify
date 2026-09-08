from unittest.mock import patch

from netlify_api import NetlifyError
from settings import build_items, main


def test_build_items_shows_build_command_and_publish_dir():
    site = {
        "admin_url": "https://app.netlify.com/projects/gbko",
        "build_settings": {"cmd": "npm run build", "dir": "dist"},
        "repo": {"repo_path": "aleksgorbenko/gbko", "repo_branch": "master"},
        "custom_domain": "aleksgorbenko.dev",
        "force_ssl": True,
        "plan": "pro",
    }
    items = build_items(site)
    values = {i["title"]: i["subtitle"] for i in items}
    assert values["Build command"] == "npm run build"
    assert values["Publish directory"] == "dist"
    assert values["Repository"] == "aleksgorbenko/gbko @ master"
    assert values["Custom domain"] == "aleksgorbenko.dev"
    assert values["Force HTTPS"] == "Yes"
    assert values["Plan"] == "pro"


def test_build_items_falls_back_to_repo_fields_when_build_settings_empty():
    site = {"repo": {"cmd": "make build", "dir": "public"}}
    items = build_items(site)
    values = {i["title"]: i["subtitle"] for i in items}
    assert values["Build command"] == "make build"
    assert values["Publish directory"] == "public"


def test_build_items_shows_not_set_for_missing_values():
    items = build_items({})
    assert all(
        i["subtitle"] == "(not set)" for i in items if i["title"] != "Force HTTPS"
    )


def test_build_items_cmd_mod_opens_admin_url():
    site = {"admin_url": "https://app.netlify.com/projects/gbko"}
    items = build_items(site)
    assert all(i["mods"]["cmd"]["arg"] == site["admin_url"] for i in items)


def test_main_errors_when_token_missing(capsys):
    with patch.dict("os.environ", {}, clear=True):
        main([])
    assert "token" in capsys.readouterr().out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"}, clear=True)
def test_main_errors_when_no_site_selected(capsys):
    main([])
    assert "no site selected" in capsys.readouterr().out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token", "SITE_ID": "site-1"})
@patch("settings.netlify_api.get_site", side_effect=NetlifyError("boom"))
def test_main_surfaces_netlify_error(_mock_get, capsys):
    main([])
    assert "boom" in capsys.readouterr().out


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token", "SITE_ID": "site-1"})
@patch("settings.netlify_api.get_site", return_value={"plan": "pro"})
def test_main_emits_settings_items(_mock_get, capsys):
    main([])
    assert "pro" in capsys.readouterr().out
