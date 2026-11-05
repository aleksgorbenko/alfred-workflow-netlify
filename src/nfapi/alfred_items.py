from datetime import UTC, datetime
from typing import Any

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
SEPARATOR = "・"

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400


def item(  # noqa: PLR0913
    title: str,
    *,
    subtitle: str = "",
    valid: bool = True,
    autocomplete: str | None = None,
    variables: dict[str, str] | None = None,
    mods: dict[str, dict[str, Any]] | None = None,
    text: dict[str, str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"title": title, "subtitle": subtitle, "valid": valid}
    if autocomplete is not None:
        result["autocomplete"] = autocomplete
    if variables is not None:
        result["variables"] = variables
    if mods is not None:
        result["mods"] = mods
    if text is not None:
        result["text"] = text
    return result


def notice(title: str, subtitle: str = "") -> dict[str, Any]:
    return item(title, subtitle=subtitle, valid=False)


def action(name: str, target: str) -> dict[str, str]:
    return {"action": name, "target": target}


def mod(subtitle: str, name: str, target: str) -> dict[str, Any]:
    if not target:
        return {"valid": False, "subtitle": f"{subtitle} (not available)"}
    return {"valid": True, "subtitle": subtitle, "variables": action(name, target)}


def joined(*parts: str) -> str:
    return SEPARATOR.join(part for part in parts if part)


def relative_time(iso_timestamp: str) -> str:
    then = datetime.fromisoformat(iso_timestamp)
    seconds = (datetime.now(UTC) - then).total_seconds()
    if seconds < SECONDS_PER_MINUTE:
        return "just now"
    if seconds < SECONDS_PER_HOUR:
        return f"{int(seconds // SECONDS_PER_MINUTE)}m ago"
    if seconds < SECONDS_PER_DAY:
        return f"{int(seconds // SECONDS_PER_HOUR)}h ago"
    return f"{int(seconds // SECONDS_PER_DAY)}d ago"


def site_title(site: dict[str, Any]) -> str:
    return site.get("custom_domain") or site["name"]


def site_state(site: dict[str, Any]) -> str:
    published: dict[str, Any] = site.get("published_deploy") or {}
    return STATE_EMOJI.get(published.get("state", ""), "🟡")


def live_url(site: dict[str, Any]) -> str:
    return site.get("ssl_url") or site.get("url", "")


def deploy_state(deploy: dict[str, Any]) -> str:
    state = deploy.get("state", "")
    emoji = STATE_EMOJI.get(state, "🟡" if state in ACTIVE_STATES else "⚪")
    message = deploy.get("error_message") if state == "error" else ""
    return f"{emoji} {state}" + (f" - {message}" if message else "")


def deploy_title(deploy: dict[str, Any]) -> str:
    parts = [deploy.get("context", ""), deploy.get("branch", "")]
    title = " / ".join(part for part in parts if part) or deploy["id"]
    if deploy.get("created_at"):
        title += f" · {relative_time(deploy['created_at'])}"
    return title


def commit_message(deploy: dict[str, Any]) -> str:
    return deploy.get("title") or deploy.get("commit_message") or ""


def is_active(deploy: dict[str, Any]) -> bool:
    return deploy.get("state", "") in ACTIVE_STATES
