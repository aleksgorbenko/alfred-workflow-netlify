import json
from unittest.mock import patch

from deploy_detail import main


def _fields(**overrides):
    base = {
        "DEPLOY_SSL_URL": "https://d1--gbko.netlify.app",
        "BUILD_PAGE_URL": "https://app.netlify.com/projects/gbko/deploys/d1",
        "STATE": "ready",
        "ERROR_MESSAGE": "",
        "BRANCH": "master",
        "CONTEXT": "production",
        "COMMIT_REF": "abc1234567",
        "COMMIT_URL": "https://github.com/aleksgorbenko/gbko/commit/abc1234567",
        "COMMIT_MESSAGE": "Fix homepage typo",
        "COMMITTER": "aleksgorbenko",
        "FRAMEWORK": "hugo",
        "DEPLOY_TIME": "19",
        "PUBLISHED_AT": "2026-09-08T12:20:15.526Z",
    }
    base.update(overrides)
    return base


@patch.dict("os.environ", _fields())
def test_main_first_row_opens_in_browser(capsys):
    main([])
    out = capsys.readouterr().out
    assert out.startswith('{"items": [{"title": "Open in browser"')
    assert '"DETAIL_ACTION": "open"' in out


@patch.dict("os.environ", _fields())
def test_main_includes_commit_and_state(capsys):
    main([])
    out = capsys.readouterr().out
    assert "Fix homepage typo" in out
    assert "hugo" in out
    assert "aleksgorbenko" in out


@patch.dict("os.environ", _fields(STATE="error", ERROR_MESSAGE="build failed"))
def test_main_state_row_includes_error_message(capsys):
    main([])
    items = json.loads(capsys.readouterr().out)["items"]
    state_row = next(i for i in items if i["title"] == "State")
    assert state_row["subtitle"] == "error - build failed"
