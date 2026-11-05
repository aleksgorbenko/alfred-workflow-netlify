import json
from typing import TYPE_CHECKING, Any

from netlify_api import NetlifyClient
from workflow import build_deps, loading_label, main, run_command

if TYPE_CHECKING:
    import pytest


def test_build_deps_without_token_has_no_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NETLIFY_TOKEN", raising=False)
    assert build_deps().source is None


def test_build_deps_with_token_uses_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NETLIFY_TOKEN", "token")
    assert build_deps().source == NetlifyClient("token")


def test_main_prints_items(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("NETLIFY_TOKEN", raising=False)
    main([])
    assert json.loads(capsys.readouterr().out)["items"][0]["valid"] is False


def test_main_performs_action(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("NETLIFY_TOKEN", raising=False)
    monkeypatch.setenv("action", "trigger_deploy")
    monkeypatch.setenv("target", "site-1")
    main(["--perform"])
    assert capsys.readouterr().out.startswith("Set your Netlify token")


def test_run_command_passes_input(capfd: pytest.CaptureFixture[str]) -> None:
    run_command(["/bin/cat"], "text")
    assert capfd.readouterr().out == "text"


def served(*_args: object, **_kwargs: object) -> dict[str, Any]:
    return {"items": [{"title": "x"}]}


def test_main_serves_a_loading_row_then_the_view(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("NETLIFY_TOKEN", "token")
    monkeypatch.setattr("workflow.serve", served)
    main(["site > "])
    assert json.loads(capsys.readouterr().out)["items"][0]["title"] == "x"


def test_job_stores_the_view(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NETLIFY_TOKEN", "token")
    stored: dict[str, Any] = {}

    def store(_directory: object, query: str, payload: dict[str, Any]) -> None:
        stored[query] = payload

    monkeypatch.setattr("workflow.run", served)
    monkeypatch.setattr("workflow.finish", store)
    main(["--job", "q"])
    assert stored == {"q": {"items": [{"title": "x"}]}}


def test_job_stores_an_error_row_when_the_view_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NETLIFY_TOKEN", "token")
    stored: dict[str, Any] = {}

    def store(_directory: object, query: str, payload: dict[str, Any]) -> None:
        stored[query] = payload

    def fail(*_args: object) -> dict[str, Any]:
        msg = "boom"
        raise RuntimeError(msg)

    monkeypatch.setattr("workflow.run", fail)
    monkeypatch.setattr("workflow.finish", store)
    main(["--job", "q"])
    assert stored["q"]["items"][0]["title"] == "boom"


def test_loading_labels_name_what_is_loading() -> None:
    assert loading_label("") == "Loading sites…"
    assert loading_label("shop > ") == "Loading shop…"
    assert loading_label("shop > builds") == "Loading builds…"
    assert loading_label("shop > builds > d1") == "Loading build…"
    assert loading_label("shop > env") == "Loading environment variables…"
    assert loading_label("shop > settings") == "Loading settings…"
