from alfred_items import (
    deploy_item,
    envvar_item,
    error_item,
    item,
    menu_item,
    settings_item,
    site_item,
)


def test_item_omits_icon_by_default():
    assert "icon" not in item(title="Title")


def test_item_omits_mods_by_default():
    assert "mods" not in item(title="Title")


def test_error_item_is_invalid():
    result = error_item("Something went wrong")
    assert result["valid"] is False
    assert result["title"] == "Something went wrong"


def test_site_item_ready_state_shows_green():
    site = {
        "id": "site-1",
        "name": "my-site",
        "account_id": "acc-1",
        "admin_url": "https://app.netlify.com/sites/my-site",
        "ssl_url": "https://my-site.netlify.app",
        "published_deploy": {"state": "ready"},
    }
    result = site_item(site)
    assert result["subtitle"] == "🟢 my-site"
    assert result["arg"] == "site-1"
    assert result["variables"] == {"SITE_ID": "site-1", "ACCOUNT_ID": "acc-1"}
    assert result["mods"]["cmd"]["arg"] == "https://app.netlify.com/sites/my-site"
    assert result["mods"]["alt"]["arg"] == "https://my-site.netlify.app"


def test_site_item_error_state_shows_red():
    site = {
        "id": "site-1",
        "name": "my-site",
        "published_deploy": {"state": "error"},
    }
    result = site_item(site)
    assert result["subtitle"].startswith("🔴")


def test_site_item_no_published_deploy_shows_yellow():
    site = {"id": "site-1", "name": "my-site"}
    result = site_item(site)
    assert result["subtitle"].startswith("🟡")


def test_site_item_prefers_custom_domain_as_title():
    site = {"id": "site-1", "name": "my-site", "custom_domain": "example.com"}
    result = site_item(site)
    assert result["title"] == "example.com"


def test_deploy_item_ready_state():
    deploy = {
        "id": "d1",
        "state": "ready",
        "branch": "main",
        "context": "production",
        "admin_url": "https://app.netlify.com/projects/my-site",
        "deploy_ssl_url": "https://d1--my-site.netlify.app",
    }
    result = deploy_item(deploy)
    assert result["subtitle"] == "🟢 ready"
    assert result["arg"] == "https://app.netlify.com/projects/my-site/deploys/d1"
    assert result["mods"]["cmd"]["arg"] == "https://d1--my-site.netlify.app"
    assert "ctrl" not in result["mods"]


def test_deploy_item_error_state_includes_message():
    deploy = {
        "id": "d1",
        "state": "error",
        "error_message": "Build script returned non-zero exit code",
    }
    result = deploy_item(deploy)
    assert result["subtitle"] == "🔴 error — Build script returned non-zero exit code"


def test_deploy_item_builds_distinct_url_per_deploy_from_shared_site_admin_url():
    # real Netlify API returns the SAME admin_url (site dashboard) on every
    # deploy in a site's deploy list - the per-deploy page is admin_url + /deploys/{id}
    shared_admin_url = "https://app.netlify.com/projects/gbko"
    older = deploy_item(
        {"id": "old-id", "state": "ready", "admin_url": shared_admin_url}
    )
    newer = deploy_item(
        {"id": "new-id", "state": "ready", "admin_url": shared_admin_url}
    )
    assert older["arg"] == "https://app.netlify.com/projects/gbko/deploys/old-id"
    assert newer["arg"] == "https://app.netlify.com/projects/gbko/deploys/new-id"
    assert older["arg"] != newer["arg"]


def test_deploy_item_active_state_has_cancel_mod():
    deploy = {"id": "d1", "state": "building"}
    result = deploy_item(deploy)
    assert result["subtitle"].startswith("🟡")
    assert result["mods"]["ctrl"]["arg"] == "d1"


def test_deploy_item_title_includes_relative_time():
    from datetime import UTC, datetime, timedelta

    ten_minutes_ago = (
        (datetime.now(UTC) - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
    )
    deploy = {
        "id": "d1",
        "state": "ready",
        "branch": "main",
        "created_at": ten_minutes_ago,
    }
    result = deploy_item(deploy)
    assert "10m ago" in result["title"]


def test_envvar_item_shows_value_and_scopes():
    env_var = {
        "key": "API_KEY",
        "scopes": ["builds", "functions"],
        "values": [{"value": "abc123"}],
    }
    result = envvar_item(env_var)
    assert result["title"] == "API_KEY"
    assert "abc123" in result["subtitle"]
    assert result["arg"] == "API_KEY=abc123"
    assert result["mods"]["cmd"]["arg"] == "abc123"


def test_envvar_item_masks_secret_values():
    env_var = {"key": "SECRET", "is_secret": True, "values": [{"value": ""}]}
    result = envvar_item(env_var)
    assert "not readable" in result["subtitle"]


def test_menu_item_sets_site_action_variable():
    result = menu_item("Builds", "Recent builds", "builds")
    assert result["title"] == "Builds"
    assert result["arg"] == "builds"
    assert result["variables"] == {"SITE_ACTION": "builds"}


def test_settings_item_shows_value_and_opens_admin_url_on_cmd():
    result = settings_item("Plan", "pro", "https://app.netlify.com/projects/gbko")
    assert result["subtitle"] == "pro"
    assert result["mods"]["cmd"]["arg"] == "https://app.netlify.com/projects/gbko"


def test_settings_item_shows_not_set_for_empty_value():
    result = settings_item("Plan", "", "https://app.netlify.com/projects/gbko")
    assert result["subtitle"] == "(not set)"
