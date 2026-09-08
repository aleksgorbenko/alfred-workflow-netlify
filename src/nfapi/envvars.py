import os
import sys

import netlify_api
from alfred_items import emit, envvar_item, error_item
from netlify_api import NetlifyError


def build_items(env_vars: list[dict]) -> list[dict]:
    if not env_vars:
        return [error_item("No environment variables set for this site")]
    ordered = sorted(env_vars, key=lambda env_var: env_var.get("key", ""))
    return [envvar_item(env_var) for env_var in ordered]


def main(argv: list[str]) -> None:  # noqa: ARG001
    token = os.environ.get("NETLIFY_TOKEN", "")
    if not token:
        emit([error_item("Set your Netlify token in the workflow configuration")])
        return

    site_id = os.environ.get("SITE_ID", "")
    account_id = os.environ.get("ACCOUNT_ID", "")
    if not site_id or not account_id:
        emit([error_item("No site selected")])
        return

    try:
        env_vars = netlify_api.get_env_vars(account_id, site_id, token)
    except NetlifyError as error:
        emit([error_item(str(error))])
        return

    emit(build_items(env_vars))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
