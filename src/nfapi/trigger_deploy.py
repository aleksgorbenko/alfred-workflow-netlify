import os
import sys

import netlify_api
from netlify_api import NetlifyError


def main(argv: list[str]) -> None:
    site_id = argv[0].strip() if argv else ""
    token = os.environ.get("NETLIFY_TOKEN", "")

    if not token:
        print("Set your Netlify token in the workflow configuration")
        return
    if not site_id:
        print("No site selected")
        return

    try:
        netlify_api.create_site_build(site_id, token)
    except NetlifyError as error:
        print(f"Failed to trigger deploy: {error}")
        return

    print("Deploy triggered")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
