import os
import sys

import netlify_api
from netlify_api import NetlifyError


def main(argv: list[str]) -> None:
    deploy_id = argv[0].strip() if argv else ""
    token = os.environ.get("NETLIFY_TOKEN", "")

    if not token:
        sys.stdout.write("Set your Netlify token in the workflow configuration\n")
        return
    if not deploy_id:
        sys.stdout.write("No build selected\n")
        return

    try:
        netlify_api.cancel_site_deploy(deploy_id, token)
    except NetlifyError as error:
        sys.stdout.write(f"Failed to cancel build: {error}\n")
        return

    sys.stdout.write("Build cancelled\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
