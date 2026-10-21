import json
import urllib.error
from email.message import Message
from unittest.mock import MagicMock, patch

import pytest
from netlify_api import (
    NetlifyAuthError,
    NetlifyClient,
    NetlifyError,
    cancel_site_deploy,
    create_site_build,
    get_env_vars,
    get_site,
    list_site_deploys,
    list_sites,
)


def mock_response(body: object, headers: dict[str, str] | None = None) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(body).encode()
    response.headers = headers or {}
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


@patch("netlify_api.urllib.request.urlopen")
def test_list_sites_sends_bearer_auth_header(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response([])
    list_sites("secret-token")

    request = mock_urlopen.call_args[0][0]
    assert request.get_header("Authorization") == "Bearer secret-token"
    assert request.get_header("User-agent")


@patch("netlify_api.urllib.request.urlopen")
def test_list_sites_raises_auth_error_on_401(mock_urlopen: MagicMock) -> None:
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="", code=401, msg="Unauthorized", hdrs=Message(), fp=None
    )
    with pytest.raises(NetlifyAuthError):
        list_sites("bad-token")


@patch("netlify_api.urllib.request.urlopen")
def test_list_sites_raises_netlify_error_on_other_http_error(
    mock_urlopen: MagicMock,
) -> None:
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="", code=500, msg="Server Error", hdrs=Message(), fp=None
    )
    with pytest.raises(NetlifyError, match="500"):
        list_sites("token")


@patch("netlify_api.urllib.request.urlopen")
def test_list_sites_raises_netlify_error_on_url_error(mock_urlopen: MagicMock) -> None:
    mock_urlopen.side_effect = urllib.error.URLError("no network")
    with pytest.raises(NetlifyError):
        list_sites("token")


@patch("netlify_api.urllib.request.urlopen")
def test_list_sites_returns_results(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response([{"id": "1", "name": "site-a"}])
    result = list_sites("token")
    assert result == [{"id": "1", "name": "site-a"}]


@patch("netlify_api.urllib.request.urlopen")
def test_list_sites_follows_link_header_pagination(mock_urlopen: MagicMock) -> None:
    page_one = mock_response(
        [{"id": "1"}],
        headers={"Link": '<https://api.netlify.com/api/v1/sites?page=2>; rel="next"'},
    )
    page_two = mock_response([{"id": "2"}], headers={})
    mock_urlopen.side_effect = [page_one, page_two]

    expected_page_count = 2
    result = list_sites("token")
    assert result == [{"id": "1"}, {"id": "2"}]
    assert mock_urlopen.call_count == expected_page_count


@patch("netlify_api.urllib.request.urlopen")
def test_list_sites_is_cached_across_calls(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response([{"id": "1"}])
    list_sites("token")
    list_sites("token")
    assert mock_urlopen.call_count == 1


@patch("netlify_api.urllib.request.urlopen")
def test_list_site_deploys_hits_correct_path(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response([{"id": "d1", "state": "ready"}])
    result = list_site_deploys("site-123", "token")
    assert result == [{"id": "d1", "state": "ready"}]

    request = mock_urlopen.call_args[0][0]
    assert "/sites/site-123/deploys" in request.full_url


@patch("netlify_api.urllib.request.urlopen")
def test_create_site_build_posts_to_builds_endpoint(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response({"id": "build-1"})
    result = create_site_build("site-123", "token")
    assert result == {"id": "build-1"}

    request = mock_urlopen.call_args[0][0]
    assert request.get_method() == "POST"
    assert request.full_url == "https://api.netlify.com/api/v1/sites/site-123/builds"


@patch("netlify_api.urllib.request.urlopen")
def test_cancel_site_deploy_posts_to_cancel_endpoint(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response({"id": "deploy-1", "state": "error"})
    result = cancel_site_deploy("deploy-1", "token")
    assert result == {"id": "deploy-1", "state": "error"}

    request = mock_urlopen.call_args[0][0]
    assert request.get_method() == "POST"
    assert request.full_url == "https://api.netlify.com/api/v1/deploys/deploy-1/cancel"


@patch("netlify_api.urllib.request.urlopen")
def test_get_env_vars_includes_site_id_query_param(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response([{"key": "FOO"}])
    result = get_env_vars("account-1", "site-123", "token")
    assert result == [{"key": "FOO"}]

    request = mock_urlopen.call_args[0][0]
    assert "/accounts/account-1/env" in request.full_url
    assert "site_id=site-123" in request.full_url


@patch("netlify_api.urllib.request.urlopen")
def test_get_env_vars_is_cached_across_calls(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response([{"key": "FOO"}])
    get_env_vars("account-1", "site-123", "token")
    get_env_vars("account-1", "site-123", "token")
    assert mock_urlopen.call_count == 1


@patch("netlify_api.urllib.request.urlopen")
def test_get_site_hits_correct_path(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response({"id": "site-123", "plan": "pro"})
    result = get_site("site-123", "token")
    assert result == {"id": "site-123", "plan": "pro"}

    request = mock_urlopen.call_args[0][0]
    assert request.full_url == "https://api.netlify.com/api/v1/sites/site-123"


@patch("netlify_api.urllib.request.urlopen")
def test_get_site_is_cached_across_calls(mock_urlopen: MagicMock) -> None:
    mock_urlopen.return_value = mock_response({"id": "site-123"})
    get_site("site-123", "token")
    get_site("site-123", "token")
    assert mock_urlopen.call_count == 1


def test_client_delegates_with_its_token() -> None:
    client = NetlifyClient("token")
    with (
        patch("netlify_api.list_sites", return_value=[]) as sites,
        patch("netlify_api.get_site", return_value={}) as site,
        patch("netlify_api.list_site_deploys", return_value=[]) as deploys,
        patch("netlify_api.get_env_vars", return_value=[]) as env_vars,
        patch("netlify_api.create_site_build") as trigger,
        patch("netlify_api.cancel_site_deploy") as cancel,
    ):
        assert client.sites() == []
        assert client.site("s") == {}
        assert client.deploys("s") == []
        assert client.env_vars("a", "s") == []
        client.trigger_deploy("s")
        client.cancel_build("d")
    sites.assert_called_once_with("token")
    site.assert_called_once_with("s", "token")
    deploys.assert_called_once_with("s", "token")
    env_vars.assert_called_once_with("a", "s", "token")
    trigger.assert_called_once_with("s", "token")
    cancel.assert_called_once_with("d", "token")
