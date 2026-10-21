import json
from typing import TYPE_CHECKING

from netlify_api import NetlifyClient
from workflow import build_deps, main, run_command

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
