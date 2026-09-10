import http
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from cache import cached

API_BASE = "https://api.netlify.com/api/v1"
USER_AGENT = "AlfredNetlifyWorkflow/1.0 +https://github.com/aleksgorbenko/alfred-workflow-netlify"

SITES_TTL = 300
SITE_TTL = 300
DEPLOYS_TTL = 45
ENV_VARS_TTL = 300

_LINK_NEXT = re.compile(r'<([^>]+)>;\s*rel="next"')


class NetlifyError(Exception):
    pass


class NetlifyAuthError(NetlifyError):
    pass


def _request(method: str, url: str, token: str) -> tuple[dict | list, dict]:
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read()
            body = json.loads(raw) if raw else {}
            return body, dict(response.headers)
    except urllib.error.HTTPError as error:
        if error.code == http.HTTPStatus.UNAUTHORIZED:
            raise NetlifyAuthError("Invalid or missing Netlify API token") from error
        raise NetlifyError(
            f"Netlify API returned HTTP {error.code} for {url}"
        ) from error
    except urllib.error.URLError as error:
        raise NetlifyError(
            f"Could not reach Netlify API ({url}): {error.reason}"
        ) from error


def _get(url: str, token: str) -> dict | list:
    return _request("GET", url, token)[0]


def _post(url: str, token: str) -> dict | list:
    return _request("POST", url, token)[0]


def _get_paginated(path: str, token: str, params: dict[str, str]) -> list[dict]:
    query = urllib.parse.urlencode({**params, "per_page": "100"})
    url = f"{API_BASE}/{path}?{query}"
    entries: list[dict] = []
    while url:
        body, headers = _request("GET", url, token)
        entries.extend(body)
        link = headers.get("Link", "")
        match = _LINK_NEXT.search(link)
        url = match.group(1) if match else None
    return entries


def list_sites(token: str) -> list[dict]:
    return cached(
        f"{API_BASE}/sites", SITES_TTL, lambda: _get_paginated("sites", token, {})
    )


def get_site(site_id: str, token: str) -> dict:
    url = f"{API_BASE}/sites/{site_id}"
    return cached(url, SITE_TTL, lambda: _get(url, token))


def list_site_deploys(site_id: str, token: str) -> list[dict]:
    url = f"{API_BASE}/sites/{site_id}/deploys"
    return cached(
        url, DEPLOYS_TTL, lambda: _get_paginated(f"sites/{site_id}/deploys", token, {})
    )


def create_site_build(site_id: str, token: str) -> dict:
    return _post(f"{API_BASE}/sites/{site_id}/builds", token)


def cancel_site_deploy(deploy_id: str, token: str) -> dict:
    return _post(f"{API_BASE}/deploys/{deploy_id}/cancel", token)


def get_env_vars(account_id: str, site_id: str, token: str) -> list[dict]:
    query = urllib.parse.urlencode({"site_id": site_id})
    url = f"{API_BASE}/accounts/{account_id}/env?{query}"
    return cached(url, ENV_VARS_TTL, lambda: _get(url, token))
