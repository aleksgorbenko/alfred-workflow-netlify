import json
import os
import subprocess
import sys

from alfred_items import notice
from app import Deps, perform, run
from async_view import finish, job_command, serve, settle
from cache import cache_dir
from netlify_api import NetlifyClient
from router import parse

LOADING = {
    "sites": "Loading sites…",
    "builds": "Loading builds…",
    "deploy": "Loading build…",
    "env": "Loading environment variables…",
    "settings": "Loading settings…",
}


def loading_label(query: str) -> str:
    route = parse(query)
    if route.page == "site":
        return f"Loading {route.site}…"
    return LOADING[route.page]


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
    if argv[:1] == ["--job"]:
        _job(argv[1] if len(argv) > 1 else "", deps)
        return
    query = argv[0] if argv else ""
    if deps.source is None:
        sys.stdout.write(json.dumps(run(query, deps), ensure_ascii=False))
        return
    payload = serve(
        query,
        directory=cache_dir(),
        command=job_command(__file__, query),
        label=loading_label(query),
    )
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def _job(query: str, deps: Deps) -> None:
    if not settle(cache_dir(), query):
        return
    try:
        payload = run(query, deps)
    except Exception as error:  # noqa: BLE001
        payload = {"items": [notice(str(error))]}
    finish(cache_dir(), query, payload)


if __name__ == "__main__":
    main(sys.argv[1:])
