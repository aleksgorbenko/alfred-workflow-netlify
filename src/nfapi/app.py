from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from alfred_items import (
    action,
    commit_message,
    deploy_state,
    deploy_title,
    is_active,
    item,
    joined,
    live_url,
    mod,
    notice,
    relative_time,
    site_state,
    site_title,
)
from netlify_api import NetlifyError
from router import BUILDS, Route, drill, parse

if TYPE_CHECKING:
    from collections.abc import Callable

SETUP_HINT = "Set your Netlify token in the workflow configuration"
NOT_SET = "(not set)"
OPEN = "open"
COPY = "copy"
TRIGGER = "trigger_deploy"
CANCEL = "cancel_build"
MESSAGES = {
    COPY: "Copied to clipboard",
    TRIGGER: "Deploy triggered",
    CANCEL: "Build cancelled",
}
FAILURES = {TRIGGER: "Failed to trigger deploy", CANCEL: "Failed to cancel build"}

Row = dict[str, Any]


class NetlifySource(Protocol):
    def sites(self) -> list[dict[str, Any]]: ...
    def site(self, site_id: str) -> dict[str, Any]: ...
    def deploys(self, site_id: str) -> list[dict[str, Any]]: ...
    def env_vars(self, account_id: str, site_id: str) -> list[dict[str, Any]]: ...
    def trigger_deploy(self, site_id: str) -> None: ...
    def cancel_build(self, deploy_id: str) -> None: ...


@dataclass(frozen=True)
class Deps:
    source: NetlifySource | None
    run_command: Callable[[list[str], str], None]


def _matches(text: str, *fields: str) -> bool:
    wanted = text.casefold()
    return not wanted or any(wanted in field.casefold() for field in fields)


def _back(path: str) -> str:
    return f"{path} ".lstrip()


def _header(row: Row, back: str, url: str, hint: str) -> Row:
    return row | {
        "valid": bool(url),
        "autocomplete": back,
        "subtitle": joined(row["subtitle"], hint),
        "variables": action(OPEN, url),
    }


def _site_row(site: dict[str, Any]) -> Row:
    return item(
        site_title(site),
        subtitle=f"{site_state(site)} {site['name']}",
        valid=False,
        autocomplete=drill("", site["name"]),
        mods={
            "cmd": mod("Open dashboard", OPEN, site.get("admin_url", "")),
            "alt": mod("Open live site", OPEN, live_url(site)),
            "ctrl": mod("Trigger new deploy", TRIGGER, site["id"]),
        },
    )


def _sites(route: Route, source: NetlifySource) -> list[Row]:
    sites = sorted(
        (
            site
            for site in source.sites()
            if _matches(route.text, site["name"], site.get("custom_domain") or "")
        ),
        key=lambda site: site["name"],
    )
    if not sites:
        if route.text:
            return [notice(f"No Netlify sites match '{route.text}'")]
        return [notice("No Netlify sites found")]
    return [_site_row(site) for site in sites]


def _find_site(route: Route, source: NetlifySource) -> dict[str, Any] | None:
    return next((site for site in source.sites() if site["name"] == route.site), None)


def _menu_row(title: str, subtitle: str, path: str, section: str) -> Row:
    return item(
        title, subtitle=subtitle, valid=False, autocomplete=drill(path, section)
    )


def _action_row(title: str, subtitle: str, name: str, target: str) -> Row:
    return item(title, subtitle=subtitle, valid=bool(target)) | {
        "variables": action(name, target)
    }


def _site(route: Route, site: dict[str, Any], _source: NetlifySource) -> list[Row]:
    header = _header(_site_row(site), "", site.get("admin_url", ""), "Open dashboard")
    rows = [
        _menu_row("Builds", "Recent builds with pass/fail status", route.path, BUILDS),
        _menu_row("Environment variables", "This site's variables", route.path, "env"),
        _menu_row("Settings", "Build and domain settings", route.path, "settings"),
        _action_row("Open live site", live_url(site), OPEN, live_url(site)),
        _action_row(
            "Trigger deploy", "Start a new production build", TRIGGER, site["id"]
        ),
    ]
    return [header, *[row for row in rows if _matches(route.text, row["title"])]]


def _section_header(title: str, site: dict[str, Any], page: str) -> Row:
    url = site.get("admin_url", "")
    target = f"{url.rstrip('/')}/{page}" if url else ""
    row = item(title, subtitle=site_title(site))
    return _header(row, drill("", site["name"]), target, "Open in Netlify")


def _build_page_url(site: dict[str, Any], deploy: dict[str, Any]) -> str:
    url = site.get("admin_url", "")
    return f"{url.rstrip('/')}/deploys/{deploy['id']}" if url else ""


def _deploy_row(deploy: dict[str, Any], path: str) -> Row:
    mods = {
        "cmd": mod("Open deploy preview", OPEN, deploy.get("deploy_ssl_url", "")),
    }
    if is_active(deploy):
        mods["ctrl"] = mod("Cancel this build", CANCEL, deploy["id"])
    return item(
        deploy_title(deploy),
        subtitle=joined(deploy_state(deploy), commit_message(deploy)),
        valid=False,
        autocomplete=drill(path, deploy["id"]),
        mods=mods,
    )


def _newest_first(deploys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        deploys, key=lambda deploy: deploy.get("created_at", ""), reverse=True
    )


def _builds(route: Route, site: dict[str, Any], source: NetlifySource) -> list[Row]:
    header = _section_header("Builds", site, "deploys")
    deploys = [
        deploy
        for deploy in _newest_first(source.deploys(site["id"]))
        if _matches(
            route.text,
            deploy_title(deploy),
            deploy.get("state", ""),
            commit_message(deploy),
        )
    ]
    if not deploys:
        return [header, notice("No builds found for this site")]
    return [header, *[_deploy_row(deploy, route.path) for deploy in deploys]]


def _detail_row(title: str, subtitle: str, value: str, name: str = COPY) -> Row:
    return item(title, subtitle=subtitle or NOT_SET, valid=bool(value)) | {
        "variables": action(name, value)
    }


def _detail_rows(deploy: dict[str, Any], build_page: str) -> list[Row]:
    branch = deploy.get("branch", "")
    context = deploy.get("context", "")
    branch_text = f"{branch} ({context})" if context else branch
    commit_url = deploy.get("commit_url", "")
    deploy_time = deploy.get("deploy_time")
    time_text = f"{deploy_time}s" if deploy_time else ""
    published = deploy.get("published_at") or ""
    preview = deploy.get("deploy_ssl_url", "")
    rows = [
        _detail_row("Open in browser", preview, preview, OPEN),
        _detail_row("Build log", build_page, build_page, OPEN),
        _detail_row(
            "Commit",
            commit_message(deploy),
            commit_url or deploy.get("commit_ref", ""),
            OPEN if commit_url else COPY,
        ),
        _detail_row("Branch", branch_text, branch_text),
        _detail_row("State", deploy_state(deploy), deploy.get("state", "")),
        _detail_row(
            "Committer", deploy.get("committer", ""), deploy.get("committer", "")
        ),
        _detail_row(
            "Framework", deploy.get("framework", ""), deploy.get("framework", "")
        ),
        _detail_row("Deploy time", time_text, time_text),
        _detail_row(
            "Published", relative_time(published) if published else "", published
        ),
    ]
    if is_active(deploy):
        rows.append(
            _detail_row("Cancel build", "Stop this build now", deploy["id"], CANCEL)
        )
    return rows


def _deploy(route: Route, site: dict[str, Any], source: NetlifySource) -> list[Row]:
    deploy = next(
        (entry for entry in source.deploys(site["id"]) if entry["id"] == route.deploy),
        None,
    )
    if deploy is None:
        return [notice(f"No build '{route.deploy}'", "Delete it to go back")]
    build_page = _build_page_url(site, deploy)
    header = _header(
        _deploy_row(deploy, route.parent),
        _back(route.parent),
        build_page,
        "Open build log",
    )
    rows = _detail_rows(deploy, build_page)
    return [header, *[row for row in rows if _matches(route.text, row["title"])]]


def _env_row(env_var: dict[str, Any]) -> Row:
    key = env_var.get("key", "")
    values: list[dict[str, Any]] = env_var.get("values") or []
    value = values[0].get("value", "") if values else ""
    secret = env_var.get("is_secret", False) or not value
    scopes = ", ".join(env_var.get("scopes") or ["all"])
    return item(
        key,
        subtitle=joined("(secret, not readable)" if secret else value, scopes),
        variables=action(COPY, f"{key}={value}"),
        mods={"cmd": mod("Copy value only", COPY, value)},
    )


def _env(route: Route, site: dict[str, Any], source: NetlifySource) -> list[Row]:
    header = _section_header("Environment variables", site, "configuration/env")
    env_vars = sorted(
        (
            env_var
            for env_var in source.env_vars(site.get("account_id", ""), site["id"])
            if _matches(route.text, env_var.get("key", ""))
        ),
        key=lambda env_var: env_var.get("key", ""),
    )
    if not env_vars:
        return [header, notice("No environment variables set for this site")]
    return [header, *[_env_row(env_var) for env_var in env_vars]]


def _repo_summary(repo: dict[str, Any]) -> str:
    repo_path = repo.get("repo_path", "")
    branch = repo.get("repo_branch", "")
    if not repo_path:
        return ""
    return f"{repo_path} @ {branch}" if branch else repo_path


def _settings(route: Route, site: dict[str, Any], source: NetlifySource) -> list[Row]:
    header = _section_header("Settings", site, "configuration/general")
    detail = source.site(site["id"])
    build: dict[str, Any] = detail.get("build_settings") or {}
    repo: dict[str, Any] = detail.get("repo") or {}
    fields = [
        ("Build command", build.get("cmd") or repo.get("cmd", "")),
        ("Publish directory", build.get("dir") or repo.get("dir", "")),
        ("Repository", _repo_summary(repo)),
        ("Custom domain", detail.get("custom_domain") or ""),
        ("Force HTTPS", "Yes" if detail.get("force_ssl") else "No"),
        ("Plan", detail.get("plan", "")),
    ]
    rows = [_detail_row(title, value, value) for title, value in fields]
    return [header, *[row for row in rows if _matches(route.text, row["title"])]]


SITE_PAGES: dict[str, Callable[[Route, dict[str, Any], NetlifySource], list[Row]]] = {
    "site": _site,
    BUILDS: _builds,
    "deploy": _deploy,
    "env": _env,
    "settings": _settings,
}


def _items(route: Route, source: NetlifySource) -> list[Row]:
    if route.page == "sites":
        return _sites(route, source)
    site = _find_site(route, source)
    if site is None:
        return [notice(f"No Netlify site named '{route.site}'", "Delete it to go back")]
    return SITE_PAGES[route.page](route, site, source)


def run(query: str, deps: Deps) -> dict[str, Any]:
    if deps.source is None:
        return {"items": [notice(SETUP_HINT)]}
    try:
        rows = _items(parse(query), deps.source)
    except NetlifyError as error:
        rows = [notice(str(error))]
    return {"items": rows}


def _remote(name: str, target: str, source: NetlifySource) -> str:
    try:
        if name == TRIGGER:
            source.trigger_deploy(target)
        else:
            source.cancel_build(target)
    except NetlifyError as error:
        return f"{FAILURES[name]}: {error}"
    return MESSAGES[name]


def perform(name: str, target: str, deps: Deps) -> str:
    if not target:
        return ""
    if name == OPEN:
        deps.run_command(["/usr/bin/open", target], "")
        return ""
    if name == COPY:
        deps.run_command(["/usr/bin/pbcopy"], target)
        return MESSAGES[COPY]
    if name not in FAILURES:
        return ""
    if deps.source is None:
        return SETUP_HINT
    return _remote(name, target, deps.source)
