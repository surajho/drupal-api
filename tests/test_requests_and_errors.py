"""Request construction and HTTP error handling."""
from __future__ import annotations

from unittest import mock

import pytest

from conftest import DOMAIN, make_response

pytestmark = pytest.mark.filterwarnings("ignore")


# --- URL building -----------------------------------------------------------

def test_relative_path_is_prefixed_with_the_domain(client):
    with mock.patch("drupal_api.drupal.requests.get", return_value=make_response(json_body={"data": []})) as get:
        client.get_entities("/jsonapi/node/article")

    assert get.call_args.args[0] == f"{DOMAIN}/jsonapi/node/article"


def test_absolute_url_is_not_prefixed_twice(client):
    absolute = f"{DOMAIN}/jsonapi/node/article"
    with mock.patch("drupal_api.drupal.requests.get", return_value=make_response(json_body={"data": []})) as get:
        client.get_entities(absolute)

    assert get.call_args.args[0] == absolute


def test_request_is_authenticated_and_verified(client):
    with mock.patch("drupal_api.drupal.requests.get", return_value=make_response(json_body={"data": []})) as get:
        client.get_entities("/jsonapi/node/article")

    assert get.call_args.kwargs["auth"] == ("user", "pass")
    assert get.call_args.kwargs["verify"] is True


def test_query_parameters_are_forwarded(client):
    params = [("filter[x][condition][path]", "name")]
    with mock.patch("drupal_api.drupal.requests.get", return_value=make_response(json_body={"data": []})) as get:
        client.get_entities("/jsonapi/node/article", parameters=params)

    assert get.call_args.kwargs["params"] == params


# --- error handling ---------------------------------------------------------

def test_http_error_raises_drupal_api_error(client):
    """A failed request must raise, not terminate the caller's process."""
    from drupal_api.exceptions import DrupalAPIError

    failure = make_response(status_code=403, json_body={"errors": [{"title": "Forbidden"}]})
    with mock.patch("drupal_api.drupal.requests.get", return_value=failure):
        with pytest.raises(DrupalAPIError) as excinfo:
            client.get_entities("/jsonapi/node/article")

    assert excinfo.value.status_code == 403


def test_error_does_not_exit_the_process(client):
    """Regression guard for the 0.3 behaviour of calling sys.exit(0) on failure."""
    from drupal_api.exceptions import DrupalAPIError

    failure = make_response(status_code=500, json_body={"errors": []})
    with mock.patch("drupal_api.drupal.requests.get", return_value=failure):
        with pytest.raises(DrupalAPIError):
            client.get_entities("/jsonapi/node/article")


def test_non_json_error_body_is_handled(client):
    """An HTML 502 must not mask the real error with a JSONDecodeError."""
    from drupal_api.exceptions import DrupalAPIError

    failure = make_response(
        status_code=502,
        text="<html><body>502 Bad Gateway</body></html>",
        content_type="text/html",
    )
    with mock.patch("drupal_api.drupal.requests.get", return_value=failure):
        with pytest.raises(DrupalAPIError) as excinfo:
            client.get_entities("/jsonapi/node/article")

    assert excinfo.value.status_code == 502
    assert "502" in str(excinfo.value)


def test_post_error_raises(client):
    from drupal_api.exceptions import DrupalAPIError

    failure = make_response(status_code=422, json_body={"errors": []})
    with mock.patch("drupal_api.drupal.requests.post", return_value=failure):
        with pytest.raises(DrupalAPIError):
            client.post_entity("/jsonapi/node/article", {"data": {}})


def test_patch_error_raises(client):
    from drupal_api.exceptions import DrupalAPIError

    failure = make_response(status_code=409, json_body={"errors": []})
    with mock.patch("drupal_api.drupal.requests.patch", return_value=failure):
        with pytest.raises(DrupalAPIError):
            client.update_entity("/jsonapi/node/article/1", {"data": {}})


def test_delete_error_raises(client):
    from drupal_api.exceptions import DrupalAPIError

    failure = make_response(status_code=404, json_body={"errors": []})
    with mock.patch("drupal_api.drupal.requests.delete", return_value=failure):
        with pytest.raises(DrupalAPIError):
            client.delete_entity("/jsonapi/node/article/1")


# --- timeouts ---------------------------------------------------------------

@pytest.mark.parametrize(
    ("method", "call"),
    [
        ("get", lambda c: c.get_entities("/jsonapi/node/article")),
        ("post", lambda c: c.post_entity("/jsonapi/node/article", {"data": {}})),
        ("patch", lambda c: c.update_entity("/jsonapi/node/article/1", {"data": {}})),
        ("delete", lambda c: c.delete_entity("/jsonapi/node/article/1")),
    ],
)
def test_every_request_sends_a_timeout(client, method, call):
    with mock.patch(
        f"drupal_api.drupal.requests.{method}",
        return_value=make_response(json_body={"data": []}),
    ) as request:
        call(client)

    assert request.call_args.kwargs.get("timeout") is not None
