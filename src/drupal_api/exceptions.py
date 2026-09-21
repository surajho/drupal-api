"""Exceptions raised by :mod:`drupal_api`."""
from __future__ import annotations

from typing import Any


class DrupalAPIError(Exception):
    """Raised when the Drupal JSON:API returns an unsuccessful response.

    Attributes
    ----------
    status_code:
        HTTP status code of the failed response, when one was received.
    url:
        URL that was requested.
    body:
        Parsed JSON error body when available, otherwise the raw text,
        truncated. Useful for surfacing Drupal's own error messages.
    response:
        The underlying :class:`requests.Response`, for callers that need it.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
        body: Any = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.body = body
        self.response = response
