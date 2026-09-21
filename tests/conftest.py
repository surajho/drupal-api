"""Shared fixtures for the drupal_api test suite."""
from __future__ import annotations

import json
from typing import Any

import pytest
import requests

DOMAIN = "https://example.invalid"


def make_response(
    *,
    status_code: int = 200,
    json_body: Any = None,
    text: str | None = None,
    content_type: str = "application/vnd.api+json",
    url: str = f"{DOMAIN}/jsonapi/node/article",
) -> requests.Response:
    """Build a real requests.Response with a canned body."""
    response = requests.Response()
    response.status_code = status_code
    response.url = url
    response.headers["Content-Type"] = content_type

    if text is not None:
        response._content = text.encode()
    elif json_body is not None:
        response._content = json.dumps(json_body).encode()
    else:
        response._content = b""

    return response


@pytest.fixture
def response_factory():
    return make_response


@pytest.fixture
def client():
    """A prod-mode client; no requests are actually sent."""
    from drupal_api.drupal import Drupal

    return Drupal(DOMAIN, "prod", "user", "pass")
