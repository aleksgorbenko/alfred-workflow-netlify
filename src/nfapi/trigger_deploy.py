import os
import sys

import netlify_api
from netlify_api import NetlifyError


def main(argv: list[str]) -> None:
    site_id = argv[0].strip() if argv else ""
    token = os.environ.get("NETLIFY_TOKEN", "")

    if not token:
        sys.stdout.write("Set your Netlify token in the workflow configuration\n")
        return
    if not site_id:
        sys.stdout.write("No site selected\n")
        return

    try:
        netlify_api.create_site_build(site_id, token)
    except NetlifyError as error:
        sys.stdout.write(f"Failed to trigger deploy: {error}\n")
        return

    sys.stdout.write("Deploy triggered\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
