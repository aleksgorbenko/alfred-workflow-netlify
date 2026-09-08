import sys

from alfred_items import emit, menu_item


def build_items() -> list[dict]:
    return [
        menu_item("Builds", "Recent builds with pass/fail status", "builds"),
        menu_item("Environment Variables", "View this site's env vars", "envvars"),
        menu_item("Settings", "Read-only build & domain settings", "settings"),
    ]


def main(argv: list[str]) -> None:  # noqa: ARG001
    emit(build_items())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
