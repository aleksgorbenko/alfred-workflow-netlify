from unittest.mock import patch

from netlify_api import NetlifyError
from trigger_deploy import main


def test_main_errors_when_token_missing(capsys):
    with patch.dict("os.environ", {}, clear=True):
        main(["site-1"])
    assert "token" in capsys.readouterr().out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"}, clear=True)
def test_main_errors_when_no_site_id(capsys):
    main([])
    assert "no site selected" in capsys.readouterr().out.lower()


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"})
@patch("trigger_deploy.netlify_api.create_site_build", side_effect=NetlifyError("boom"))
def test_main_surfaces_error(_mock_create, capsys):
    main(["site-1"])
    assert "boom" in capsys.readouterr().out


@patch.dict("os.environ", {"NETLIFY_TOKEN": "token"})
@patch("trigger_deploy.netlify_api.create_site_build", return_value={"id": "build-1"})
def test_main_confirms_trigger(mock_create, capsys):
    main(["site-1"])
    mock_create.assert_called_once_with("site-1", "token")
    assert "triggered" in capsys.readouterr().out.lower()
