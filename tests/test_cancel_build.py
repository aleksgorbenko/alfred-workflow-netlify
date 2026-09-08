from unittest.mock import patch

from cancel_build import main
from netlify_api import NetlifyError


def test_main_errors_when_token_missing(capsys):
    with patch.dict("os.environ", {}, clear=True):
        main(["deploy-1"])
    assert "token" in capsys.readouterr().out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"}, clear=True)
def test_main_errors_when_no_deploy_id(capsys):
    main([])
    assert "no build selected" in capsys.readouterr().out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"})
@patch("cancel_build.netlify_api.cancel_site_deploy", side_effect=NetlifyError("boom"))
def test_main_surfaces_error(_mock_cancel, capsys):
    main(["deploy-1"])
    assert "boom" in capsys.readouterr().out


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"})
@patch("cancel_build.netlify_api.cancel_site_deploy", return_value={"id": "deploy-1"})
def test_main_confirms_cancel(mock_cancel, capsys):
    main(["deploy-1"])
    mock_cancel.assert_called_once_with("deploy-1", "token")
    assert "cancelled" in capsys.readouterr().out.lower()
