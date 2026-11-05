from dataclasses import dataclass, field
from typing import Any

from app import SETUP_HINT, Deps, perform, run
from netlify_api import NetlifyError

ADMIN = "https://app.netlify.com/projects/example-site"
SITE: dict[str, Any] = {
    "id": "site-1",
    "name": "example-site",
    "account_id": "account-1",
    "admin_url": ADMIN,
    "ssl_url": "https://example-site.netlify.app",
    "published_deploy": {"state": "ready"},
}
OTHER: dict[str, Any] = {"id": "site-2", "name": "another", "custom_domain": "b.test"}
READY: dict[str, Any] = {
    "id": "d1",
    "state": "ready",
    "context": "production",
    "branch": "main",
    "created_at": "2026-01-01T00:00:00+00:00",
    "title": "Fix typo",
    "deploy_ssl_url": "https://d1--example-site.netlify.app",
    "commit_url": "https://example.com/commit/abc",
    "deploy_time": 19,
    "published_at": "2026-01-01T00:01:00+00:00",
}
BUILDING: dict[str, Any] = {
    "id": "d2",
    "state": "building",
    "created_at": "2026-01-02T00:00:00+00:00",
}
ENV_VARS: list[dict[str, Any]] = [
    {"key": "TOKEN", "is_secret": True, "values": []},
    {"key": "API_URL", "values": [{"value": "https://api.test"}], "scopes": ["builds"]},
]
DETAIL: dict[str, Any] = {
    "build_settings": {"cmd": "hugo", "dir": "public"},
    "repo": {"repo_path": "owner/repo", "repo_branch": "main"},
    "force_ssl": True,
    "plan": "starter",
}


@dataclass
class FakeSource:
    sites_result: list[dict[str, Any]] = field(default_factory=lambda: [SITE, OTHER])
    deploys_result: list[dict[str, Any]] = field(
        default_factory=lambda: [READY, BUILDING]
    )
    error: NetlifyError | None = None
    calls: list[tuple[str, str]] = field(default_factory=list[tuple[str, str]])

    def _check(self) -> None:
        if self.error is not None:
            raise self.error

    def sites(self) -> list[dict[str, Any]]:
        self._check()
        return self.sites_result

    def site(self, site_id: str) -> dict[str, Any]:
        self.calls.append(("site", site_id))
        return DETAIL

    def deploys(self, site_id: str) -> list[dict[str, Any]]:
        self.calls.append(("deploys", site_id))
        return self.deploys_result

    def env_vars(self, account_id: str, site_id: str) -> list[dict[str, Any]]:
        self.calls.append(("env_vars", f"{account_id}/{site_id}"))
        return ENV_VARS

    def trigger_deploy(self, site_id: str) -> None:
        self._check()
        self.calls.append(("trigger_deploy", site_id))

    def cancel_build(self, deploy_id: str) -> None:
        self._check()
        self.calls.append(("cancel_build", deploy_id))


@dataclass
class Commands:
    calls: list[tuple[list[str], str]] = field(
        default_factory=list[tuple[list[str], str]]
    )

    def __call__(self, command: list[str], text: str) -> None:
        self.calls.append((command, text))


def deps(source: FakeSource | None = None, commands: Commands | None = None) -> Deps:
    return Deps(source or FakeSource(), commands or Commands())


def rows(query: str, source: FakeSource | None = None) -> list[dict[str, Any]]:
    return run(query, deps(source))["items"]


def titles(query: str) -> list[str]:
    return [row["title"] for row in rows(query)]


def test_missing_token_shows_notice() -> None:
    result = run("", Deps(None, Commands()))
    assert result["items"][0]["title"] == SETUP_HINT


def test_sites_are_sorted_and_drill_into_site() -> None:
    items = rows("")
    assert [row["title"] for row in items] == ["b.test", "example-site"]
    assert items[1]["valid"] is False
    assert items[1]["autocomplete"] == "example-site > "
    assert items[1]["subtitle"] == "🟢 example-site"


def test_site_mods_open_and_trigger() -> None:
    mods = rows("example")[0]["mods"]
    assert mods["alt"]["variables"] == {"action": "open", "target": ADMIN}
    live = "https://example-site.netlify.app"
    assert mods["alt+ctrl"]["variables"]["target"] == live
    assert mods["cmd"]["variables"] == {"action": "trigger_deploy", "target": "site-1"}


def test_site_without_live_url_disables_mod() -> None:
    mods = rows("another")[0]["mods"]
    assert mods["alt+ctrl"]["valid"] is False


def test_sites_filter_without_match() -> None:
    assert titles("zzz") == ["No Netlify sites match 'zzz'"]


def test_no_sites() -> None:
    assert [row["title"] for row in rows("", FakeSource(sites_result=[]))] == [
        "No Netlify sites found"
    ]


def test_api_error_becomes_notice() -> None:
    source = FakeSource(error=NetlifyError("boom"))
    assert [row["title"] for row in rows("", source)] == ["boom"]


def test_unknown_site() -> None:
    assert titles("missing > ") == ["No Netlify site named 'missing'"]


def test_site_page_has_header_and_sections() -> None:
    items = rows("example-site > ")
    assert [row["title"] for row in items] == [
        "example-site",
        "Builds",
        "Environment variables",
        "Settings",
        "Open live site",
        "Trigger deploy",
    ]
    header = items[0]
    assert header["valid"] is True
    assert header["autocomplete"] == ""
    assert header["variables"] == {"action": "open", "target": ADMIN}
    assert header["subtitle"] == "🟢 example-site · ↩ Open dashboard"
    assert items[1]["autocomplete"] == "example-site > builds "


def test_site_page_filters_rows() -> None:
    assert titles("example-site > envir") == ["example-site", "Environment variables"]
    assert titles("example-site > trig") == ["example-site", "Trigger deploy"]


def test_builds_lists_newest_first_and_drill_into_deploy() -> None:
    items = rows("example-site > builds ")
    header = items[0]
    assert header["title"] == "Builds"
    assert header["autocomplete"] == "example-site > "
    assert header["variables"]["target"] == f"{ADMIN}/deploys"
    assert items[1]["autocomplete"] == "example-site > builds > d2 "
    assert items[1]["mods"]["ctrl"]["variables"] == {
        "action": "cancel_build",
        "target": "d2",
    }
    assert "ctrl" not in items[2]["mods"]
    assert items[2]["subtitle"] == "🟢 ready・Fix typo"


def test_builds_filter_and_empty() -> None:
    assert len(rows("example-site > builds typo")) == 2  # noqa: PLR2004
    assert titles("example-site > builds zzz")[1] == "No builds found for this site"


def test_deploy_detail_rows() -> None:
    items = rows("example-site > builds > d1 ")
    header = items[0]
    assert header["autocomplete"] == "example-site > builds "
    assert header["variables"]["target"] == f"{ADMIN}/deploys/d1"
    by_title = {row["title"]: row for row in items[1:]}
    assert by_title["Commit"]["variables"] == {
        "action": "open",
        "target": "https://example.com/commit/abc",
    }
    assert by_title["Branch"]["subtitle"] == "main (production)"
    assert by_title["Deploy time"]["subtitle"] == "19s"
    assert by_title["Framework"]["valid"] is False
    assert by_title["Framework"]["subtitle"] == "(not set)"
    assert "Cancel build" not in by_title


def test_active_deploy_can_be_cancelled_and_filtered() -> None:
    header, *matches = titles("example-site > builds > d2 cancel")
    assert header.startswith("d2 · ")
    assert matches == ["Cancel build"]


def test_unknown_deploy() -> None:
    assert titles("example-site > builds > nope") == ["No build 'nope'"]


def test_env_vars_sorted_and_secret_hidden() -> None:
    items = rows("example-site > env")
    assert [row["title"] for row in items] == [
        "Environment variables",
        "API_URL",
        "TOKEN",
    ]
    assert items[0]["variables"]["target"] == f"{ADMIN}/configuration/env"
    assert items[1]["subtitle"] == "https://api.test・builds"
    assert items[1]["variables"] == {
        "action": "copy",
        "target": "API_URL=https://api.test",
    }
    assert items[2]["subtitle"] == "(secret, not readable)・all"
    assert "text" not in items[2]
    assert items[1]["text"] == {
        "copy": "https://api.test",
        "largetype": "https://api.test",
    }


def test_env_vars_empty_filter() -> None:
    assert titles("example-site > env zzz")[1] == (
        "No environment variables set for this site"
    )


def test_settings_rows() -> None:
    items = rows("example-site > settings")
    by_title = {row["title"]: row["subtitle"] for row in items[1:]}
    assert by_title == {
        "Build command": "hugo",
        "Publish directory": "public",
        "Repository": "owner/repo @ main",
        "Custom domain": "(not set)",
        "Force HTTPS": "Yes",
        "Plan": "starter",
    }
    assert titles("example-site > settings plan") == ["Settings", "Plan"]


def test_perform_open_and_copy() -> None:
    commands = Commands()
    assert perform("open", "https://x.test", deps(commands=commands)) == ""
    assert perform("copy", "A=1", deps(commands=commands)) == "Copied to clipboard"
    assert commands.calls == [
        (["/usr/bin/open", "https://x.test"], ""),
        (["/usr/bin/pbcopy"], "A=1"),
    ]


def test_perform_api_actions() -> None:
    source = FakeSource()
    assert perform("trigger_deploy", "site-1", deps(source)) == "Deploy triggered"
    assert perform("cancel_build", "d2", deps(source)) == "Build cancelled"
    assert source.calls == [("trigger_deploy", "site-1"), ("cancel_build", "d2")]


def test_perform_reports_failure() -> None:
    source = FakeSource(error=NetlifyError("boom"))
    assert perform("cancel_build", "d2", deps(source)) == "Failed to cancel build: boom"


def test_perform_ignores_unknown_or_empty() -> None:
    assert perform("explode", "x", deps()) == ""
    assert perform("open", "", deps()) == ""


def test_perform_without_token() -> None:
    assert perform("trigger_deploy", "site-1", Deps(None, Commands())) == SETUP_HINT
