"""HTTP client for the Drupal JSON:API."""
from __future__ import annotations

import collections.abc
import datetime as _datetime
import json
import logging
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import requests
import urllib3
from fake_useragent import UserAgent

from drupal_api.exceptions import DrupalAPIError

logger = logging.getLogger(__name__)

#: Seconds before an individual HTTP request is abandoned.
DEFAULT_TIMEOUT = 30
#: Characters of a non-JSON error body kept for diagnostics.
ERROR_BODY_LIMIT = 500

QueryParameters = Sequence[tuple] | Mapping[str, Any]


def json_default(value: Any) -> str:
    """Serialise values ``json.dumps`` cannot handle natively.

    Dates and datetimes become ISO-8601 strings, which is what Drupal's
    JSON:API expects for date fields.
    """
    if isinstance(value, (_datetime.datetime, _datetime.date)):
        return value.isoformat()

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class Drupal:
    """Authenticated client for one Drupal site's JSON:API.

    Parameters
    ----------
    domain:
        Base URL of the site, e.g. ``https://example.com``.
    environment:
        ``"prod"`` verifies TLS certificates; ``"dev"`` disables verification
        for self-signed certificates and silences the matching warning.
    username, password:
        Credentials for HTTP basic authentication.
    timeout:
        Seconds before a request is abandoned. Defaults to
        :data:`DEFAULT_TIMEOUT`.

    Raises
    ------
    ValueError
        If ``environment`` is neither ``"prod"`` nor ``"dev"``.
    """

    def __init__(
        self,
        domain: str,
        environment: str,
        username: str,
        password: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.domain = domain
        self.timeout = timeout

        if environment == "prod":
            self.request_verification = True
        elif environment == "dev":
            self.request_verification = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        else:
            raise ValueError(
                f"Unknown Drupal environment {environment!r}; expected 'prod' or 'dev'"
            )

        self.json_api_username = username
        self.json_api_password = password
        self.default_headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    # --- internals ---------------------------------------------------------

    def _absolute_url(self, url: str) -> str:
        """Prefix ``url`` with the site domain unless it already carries it."""
        if url.startswith(self.domain):
            return url

        return self.domain + url

    @staticmethod
    def _describe_error_body(response: requests.Response) -> Any:
        """Return the response body for diagnostics, JSON when possible.

        Never raises: an error response is often HTML or empty, and failing
        here would mask the HTTP error the caller actually needs to see.
        """
        try:
            return response.json()
        except ValueError:
            text = (response.text or "").strip()
            return text[:ERROR_BODY_LIMIT] if text else None

    def _raise_for_status(self, response: requests.Response) -> None:
        """Convert an unsuccessful response into :class:`DrupalAPIError`."""
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            body = self._describe_error_body(response)
            logger.error("Drupal request failed: %s | body=%s", error, body)
            raise DrupalAPIError(
                str(error),
                status_code=response.status_code,
                url=response.url,
                body=body,
                response=response,
            ) from error

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: QueryParameters | None = None,
        data: Any = None,
    ) -> requests.Response:
        """Send one authenticated request and raise on an error status."""
        request_method = getattr(requests, method)
        response = request_method(
            url,
            headers=dict(headers if headers is not None else self.default_headers),
            params=params,
            data=data,
            verify=self.request_verification,
            auth=(self.json_api_username, self.json_api_password),
            timeout=self.timeout,
        )

        self._raise_for_status(response)
        return response

    # --- reading -----------------------------------------------------------

    def get_entities(self, url: str, **kwargs: Any) -> requests.Response:
        """Retrieve entities from ``url``.

        Parameters
        ----------
        url:
            Absolute URL, or a path such as ``/jsonapi/node/article`` which is
            resolved against the site domain.
        **kwargs:
            ``parameters`` is forwarded to ``requests`` as the query string.
            Pass a list of two-tuples to keep the order stable.

        Raises
        ------
        DrupalAPIError
            If the request fails or returns an error status.
        """
        return self._request(
            "get",
            self._absolute_url(url),
            params=kwargs.get("parameters"),
        )

    def get_drupal_entity_collection(self, url: str, **kwargs: Any) -> list:
        """Retrieve every entity from a paginated collection.

        Follows JSON:API ``next`` links until the collection is exhausted and
        returns the accumulated entities. Returns an empty list when the
        collection is empty.
        """
        entities_list: list = []
        current_url = self._absolute_url(url)
        query = kwargs.get("query")

        while True:
            entity_page = self.get_entities(current_url, parameters=query).json()
            page_data = entity_page.get("data", [])

            if not page_data:
                break

            entities_list.extend(page_data)
            logger.info(
                "Retrieved %s entities of type %s",
                len(entities_list),
                url.rstrip("/").split("/")[-1],
            )

            next_link = entity_page.get("links", {}).get("next")

            if not next_link:
                break

            current_url = next_link["href"]
            # Pagination links already carry the query string.
            query = None

        return entities_list

    # --- writing -----------------------------------------------------------

    def post_entity(
        self,
        entity_url: str,
        data_package: Any,
        file: bool = False,
        filename: str = "",
    ) -> requests.Response:
        """Create an entity, or upload a file when ``file`` is True.

        Raises
        ------
        DrupalAPIError
            If the request fails or returns an error status.
        """
        headers = dict(self.default_headers)

        if file:
            headers["Content-Disposition"] = f'file; filename="{filename}"'
            headers["Content-Type"] = "application/octet-stream"
            data = data_package
        else:
            data = json.dumps(data_package, default=json_default)

        return self._request(
            "post",
            self._absolute_url(entity_url),
            headers=headers,
            data=data,
        )

    def update_entity(self, entity_url: str, data_package: Any) -> requests.Response:
        """Patch an existing entity.

        Raises
        ------
        DrupalAPIError
            If the request fails or returns an error status.
        """
        return self._request(
            "patch",
            self._absolute_url(entity_url),
            data=json.dumps(data_package, default=json_default),
        )

    def delete_entity(self, entity_url: str) -> requests.Response:
        """Delete an entity.

        Raises
        ------
        DrupalAPIError
            If the request fails or returns an error status.
        """
        return self._request("delete", self._absolute_url(entity_url))

    # --- higher-level helpers ----------------------------------------------

    def get_taxonomy_term(
        self,
        post_url: str,
        data: dict,
        extra_data: dict | None = None,
    ) -> Any:
        """Return the taxonomy term matching ``data``, creating it if absent."""
        params = [
            ("filter[a-label][condition][path]", "name"),
            ("filter[a-label][condition][operator]", "="),
            ("filter[a-label][condition][value]", data["data"]["attributes"]["name"]),
        ]

        taxonomy_term_response = self.get_entities(post_url, parameters=params)
        existing_terms = taxonomy_term_response.json()["data"]

        if existing_terms:
            return existing_terms[0]

        data_to_send = self.merge_dicts(data, extra_data) if extra_data else data
        created_response = self.post_entity(post_url, data_to_send)

        return created_response.json()["data"]

    @staticmethod
    def merge_dicts(dict1: dict, dict2: Mapping[Any, Any]) -> dict:
        """Recursively merge ``dict2`` into ``dict1`` and return ``dict1``.

        Unlike :meth:`dict.update`, nested dictionaries are merged key by key
        rather than replaced wholesale.
        """
        for key, value in dict2.items():
            if (
                key in dict1
                and isinstance(dict1[key], dict)
                and isinstance(value, collections.abc.Mapping)
            ):
                Drupal.merge_dicts(dict1[key], value)
            else:
                dict1[key] = value

        return dict1

    def get_file_id(self, drupal_field_url: str, **kwargs: Any) -> str:
        """Return the UUID of a file, uploading it when it does not exist yet.

        Parameters
        ----------
        drupal_field_url:
            File field endpoint, e.g.
            ``/jsonapi/media/image/field_media_image``.
        file_url_or_path:
            URL or local path of the file.
        filename:
            Overrides the name derived from ``file_url_or_path``.
        local_file:
            Read from disk instead of downloading. Defaults to False.
        file_bytes:
            Pre-read content, skipping both disk and network.

        Raises
        ------
        DrupalAPIError
            If a request fails or returns an error status.
        """
        filename = kwargs.get("filename")
        file_url_or_path = kwargs.get("file_url_or_path")

        if filename is None:
            filename = [part for part in str(file_url_or_path).split("/") if part][-1]

        params = [
            ("filter[a-label][condition][path]", "filename"),
            ("filter[a-label][condition][operator]", "="),
            ("filter[a-label][condition][value]", filename),
        ]

        file_response = self.get_entities("/jsonapi/file/file", parameters=params)
        existing_files = file_response.json()["data"]

        if existing_files:
            return existing_files[0]["id"]

        file_bytes = kwargs.get("file_bytes")

        if file_bytes is None:
            file_bytes = self._get_file_bytes(
                kwargs.get("local_file", False), file_url_or_path
            )

        uploaded_file_response = self.post_entity(
            drupal_field_url, file_bytes, True, filename
        )

        return uploaded_file_response.json()["data"]["id"]

    @staticmethod
    def _get_file_bytes(local_file: bool, file_url_or_path: Any) -> bytes:
        """Read a file from disk, or download it over HTTP."""
        if local_file:
            with Path(file_url_or_path).open("rb") as file_to_read:
                return file_to_read.read()

        url = str(file_url_or_path)

        if not url.lower().startswith(("http://", "https://")):
            raise ValueError(f"Refusing to fetch non-HTTP(S) URL: {url!r}")

        try:
            # Scheme is validated above, so this is not an arbitrary-URL open.
            custom_request = urllib.request.Request(  # noqa: S310
                url, headers={"User-Agent": UserAgent().random}
            )

            with urllib.request.urlopen(custom_request, timeout=DEFAULT_TIMEOUT) as handle:  # noqa: S310
                return handle.read()
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            logger.error("Could not download %s: %s", url, error)
            raise DrupalAPIError(f"Could not download {url}: {error}", url=url) from error
