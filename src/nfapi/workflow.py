import json
import os
import subprocess
import sys

from app import Deps, perform, run
from netlify_api import NetlifyClient


def run_command(command: list[str], text: str) -> None:
    subprocess.run(command, input=text, text=True, check=False)  # noqa: S603


def build_deps() -> Deps:
    token = os.environ.get("NETLIFY_TOKEN", "")
    return Deps(NetlifyClient(token) if token else None, run_command)


def main(argv: list[str]) -> None:
    deps = build_deps()
    if argv[:1] == ["--perform"]:
        message = perform(
            os.environ.get("action", ""),  # noqa: SIM112
            os.environ.get("target", ""),  # noqa: SIM112
            deps,
        )
        sys.stdout.write(message)
        return
    query = argv[0] if argv else ""
    sys.stdout.write(json.dumps(run(query, deps), ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
