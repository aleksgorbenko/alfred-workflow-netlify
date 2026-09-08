import os
import sys

import netlify_api
from alfred_items import emit, error_item, site_item
from netlify_api import NetlifyError


def _matches(site: dict, query: str) -> bool:
    haystack = f"{site.get('name', '')} {site.get('custom_domain', '')}".lower()
    return query.lower() in haystack


def build_items(sites: list[dict], query: str) -> list[dict]:
    matches = [site for site in sites if _matches(site, query)] if query else sites
    if not matches:
        return [
            error_item(
                f"No Netlify sites match '{query}'"
                if query
                else "No Netlify sites found"
            )
        ]
    matches.sort(key=lambda site: site.get("name", ""))
    return [site_item(site) for site in matches]


def main(argv: list[str]) -> None:
    query = argv[0].strip() if argv else ""

    token = os.environ.get("NETLIFY_TOKEN", "")
    if not token:
        emit([error_item("Set your Netlify token in the workflow configuration")])
        return

    try:
        sites = netlify_api.list_sites(token)
    except NetlifyError as error:
        emit([error_item(str(error))])
        return

    emit(build_items(sites, query))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
