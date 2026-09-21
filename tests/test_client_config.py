"""How the client is configured from its constructor arguments."""
from __future__ import annotations

import pytest

from drupal_api.drupal import Drupal

DOMAIN = "https://example.invalid"


def test_prod_enables_certificate_verification():
    assert Drupal(DOMAIN, "prod", "u", "p").request_verification is True


def test_dev_disables_certificate_verification():
    assert Drupal(DOMAIN, "dev", "u", "p").request_verification is False


def test_unknown_environment_is_rejected():
    """1.0 raises ValueError; 0.3 called raise SystemExit."""
    with pytest.raises(ValueError, match="Unknown Drupal environment"):
        Drupal(DOMAIN, "staging", "u", "p")


def test_credentials_and_headers_are_stored():
    client = Drupal(DOMAIN, "prod", "user", "pass")
    assert client.json_api_username == "user"
    assert client.json_api_password == "pass"
    assert client.default_headers["Accept"] == "application/vnd.api+json"
    assert client.default_headers["Content-Type"] == "application/vnd.api+json"
