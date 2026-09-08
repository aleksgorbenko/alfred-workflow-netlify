import json
import sys
from datetime import UTC, datetime

STATE_EMOJI = {"ready": "🟢", "error": "🔴"}
ACTIVE_STATES = {
    "new",
    "enqueued",
    "building",
    "uploading",
    "uploaded",
    "processing",
    "preparing",
}

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400


def item(  # noqa: PLR0913, PLR0917
    title: str,
    subtitle: str = "",
    arg: str | None = None,
    valid: bool = True,
    icon: str | None = None,
    variables: dict[str, str] | None = None,
    mods: dict[str, dict] | None = None,
) -> dict:
    result: dict = {"title": title, "subtitle": subtitle, "valid": valid}
    if arg is not None:
        result["arg"] = arg
    if icon is not None:
        result["icon"] = {"path": icon}
    if variables is not None:
        result["variables"] = variables
    if mods is not None:
        result["mods"] = mods
    return result


def error_item(message: str) -> dict:
    return item(title=message, valid=False)


def _relative_time(iso_timestamp: str) -> str:
    then = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    seconds = (datetime.now(UTC) - then).total_seconds()
    if seconds < SECONDS_PER_MINUTE:
        return "just now"
    if seconds < SECONDS_PER_HOUR:
        return f"{int(seconds // SECONDS_PER_MINUTE)}m ago"
    if seconds < SECONDS_PER_DAY:
        return f"{int(seconds // SECONDS_PER_HOUR)}h ago"
    return f"{int(seconds // SECONDS_PER_DAY)}d ago"


def site_item(site: dict) -> dict:
    site_id = site["id"]
    name = site.get("custom_domain") or site["name"]
    published = site.get("published_deploy") or {}
    state = published.get("state", "")
    emoji = STATE_EMOJI.get(state, "🟡")
    subtitle = f"{emoji} {site['name']}"
    return item(
        title=name,
        subtitle=subtitle,
        arg=site_id,
        variables={"SITE_ID": site_id, "ACCOUNT_ID": site.get("account_id", "")},
        mods={
            "cmd": {"arg": site.get("admin_url", ""), "subtitle": "Open site settings"},
            "alt": {
                "arg": site.get("ssl_url", site.get("url", "")),
                "subtitle": "Open live site",
            },
            "ctrl": {"subtitle": "Trigger new deploy"},
            "shift": {"subtitle": "View environment variables"},
        },
    )


def deploy_item(deploy: dict) -> dict:
    state = deploy.get("state", "")
    emoji = STATE_EMOJI.get(state, "🟡" if state in ACTIVE_STATES else "⚪")
    subtitle = f"{emoji} {state}"
    if state == "error" and deploy.get("error_message"):
        subtitle += f" — {deploy['error_message']}"

    context = deploy.get("context", "")
    branch = deploy.get("branch", "")
    title_parts = [part for part in (context, branch) if part]
    title = " / ".join(title_parts) or deploy["id"]
    if deploy.get("created_at"):
        title += f" · {_relative_time(deploy['created_at'])}"

    mods = {
        "cmd": {
            "arg": deploy.get("deploy_ssl_url", ""),
            "subtitle": "Open deploy preview",
        }
    }
    if state in ACTIVE_STATES:
        mods["ctrl"] = {"arg": deploy["id"], "subtitle": "Cancel this build"}

    site_admin_url = deploy.get("admin_url", "")
    build_page_url = (
        f"{site_admin_url.rstrip('/')}/deploys/{deploy['id']}" if site_admin_url else ""
    )

    return item(
        title=title,
        subtitle=subtitle,
        arg=build_page_url,
        mods=mods,
    )


def envvar_item(env_var: dict) -> dict:
    key = env_var.get("key", "")
    values = env_var.get("values") or []
    value = values[0].get("value", "") if values else ""
    is_secret = env_var.get("is_secret", False)
    scopes = ", ".join(env_var.get("scopes") or ["all"])
    display_value = "(secret, not readable)" if is_secret or not value else value
    subtitle = f"{display_value}  ·  {scopes}"
    return item(
        title=key,
        subtitle=subtitle,
        arg=f"{key}={value}",
        mods={"cmd": {"arg": value, "subtitle": "Copy value only"}},
    )


def menu_item(label: str, subtitle: str, action: str) -> dict:
    return item(
        title=label, subtitle=subtitle, arg=action, variables={"SITE_ACTION": action}
    )


def settings_item(label: str, value: str, admin_url: str) -> dict:
    display_value = value or "(not set)"
    return item(
        title=label,
        subtitle=display_value,
        arg=display_value,
        mods={"cmd": {"arg": admin_url, "subtitle": "Open settings page"}},
    )


def emit(items: list[dict]) -> None:
    json.dump({"items": items}, sys.stdout)
