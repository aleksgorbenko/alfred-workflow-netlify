import os
import sys

import netlify_api
from alfred_items import emit, error_item, settings_item
from netlify_api import NetlifyError


def _repo_summary(site: dict) -> str:
    repo = site.get("repo") or {}
    repo_path = repo.get("repo_path", "")
    branch = repo.get("repo_branch", "")
    if not repo_path:
        return ""
    return f"{repo_path} @ {branch}" if branch else repo_path


def build_items(site: dict) -> list[dict]:
    admin_url = site.get("admin_url", "")
    build_settings = site.get("build_settings") or {}
    repo = site.get("repo") or {}

    rows = [
        ("Build command", build_settings.get("cmd") or repo.get("cmd", "")),
        ("Publish directory", build_settings.get("dir") or repo.get("dir", "")),
        ("Repository", _repo_summary(site)),
        ("Custom domain", site.get("custom_domain", "")),
        ("Force HTTPS", "Yes" if site.get("force_ssl") else "No"),
        ("Plan", site.get("plan", "")),
    ]
    return [settings_item(label, value, admin_url) for label, value in rows]


def main(argv: list[str]) -> None:  # noqa: ARG001
    token = os.environ.get("NETLIFY_TOKEN", "")
    if not token:
        emit([error_item("Set your Netlify token in the workflow configuration")])
        return

    site_id = os.environ.get("SITE_ID", "")
    if not site_id:
        emit([error_item("No site selected")])
        return

    try:
        site = netlify_api.get_site(site_id, token)
    except NetlifyError as error:
        emit([error_item(str(error))])
        return

    emit(build_items(site))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
