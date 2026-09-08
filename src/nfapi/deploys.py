import os
import sys

import netlify_api
from alfred_items import deploy_item, emit, error_item
from netlify_api import NetlifyError


def build_items(deploys: list[dict]) -> list[dict]:
    if not deploys:
        return [error_item("No builds found for this site")]
    ordered = sorted(
        deploys, key=lambda deploy: deploy.get("created_at", ""), reverse=True
    )
    return [deploy_item(deploy) for deploy in ordered]


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
        deploys = netlify_api.list_site_deploys(site_id, token)
    except NetlifyError as error:
        emit([error_item(str(error))])
        return

    emit(build_items(deploys))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
