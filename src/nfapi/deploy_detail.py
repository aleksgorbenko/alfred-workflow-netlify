import os
import sys

from alfred_items import deploy_detail_items, emit

FIELDS = (
    "DEPLOY_SSL_URL",
    "BUILD_PAGE_URL",
    "STATE",
    "ERROR_MESSAGE",
    "BRANCH",
    "CONTEXT",
    "COMMIT_REF",
    "COMMIT_URL",
    "COMMIT_MESSAGE",
    "COMMITTER",
    "FRAMEWORK",
    "DEPLOY_TIME",
    "PUBLISHED_AT",
)


def main(argv: list[str]) -> None:  # noqa: ARG001
    fields = {name: os.environ.get(name, "") for name in FIELDS}
    emit(deploy_detail_items(fields))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
