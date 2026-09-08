import os
import sys

import netlify_api
from netlify_api import NetlifyError


def main(argv: list[str]) -> None:
    deploy_id = argv[0].strip() if argv else ""
    token = os.environ.get("NETLIFY_TOKEN", "")

    if not token:
        print("Set your Netlify token in the workflow configuration")
        return
    if not deploy_id:
        print("No build selected")
        return

    try:
        netlify_api.cancel_site_deploy(deploy_id, token)
    except NetlifyError as error:
        print(f"Failed to cancel build: {error}")
        return

    print("Build cancelled")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
