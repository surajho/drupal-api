"""Pagination, dict merging, taxonomy lookup and file handling."""
from __future__ import annotations

from unittest import mock

import pytest

from conftest import DOMAIN, make_response


# --- get_drupal_entity_collection ------------------------------------------

def test_collection_follows_pagination(client):
    page_one = make_response(
        json_body={
            "data": [{"id": "1"}, {"id": "2"}],
            "links": {"next": {"href": f"{DOMAIN}/jsonapi/node/article?page=1"}},
        }
    )
    page_two = make_response(json_body={"data": [{"id": "3"}], "links": {}})

    with mock.patch("drupal_api.drupal.requests.get", side_effect=[page_one, page_two]):
        result = client.get_drupal_entity_collection("/jsonapi/node/article")

    assert [entity["id"] for entity in result] == ["1", "2", "3"]


def test_empty_collection_returns_an_empty_list(client):
    """An empty result must stay iterable and the same type as a full one."""
    empty = make_response(json_body={"data": [], "links": {}})

    with mock.patch("drupal_api.drupal.requests.get", return_value=empty):
        result = client.get_drupal_entity_collection("/jsonapi/node/article")

    assert result == []
    assert isinstance(result, list)


# --- merge_dicts ------------------------------------------------------------

def test_merge_dicts_merges_flat_keys(client):
    assert client.merge_dicts({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_merge_dicts_overwrites_scalars(client):
    assert client.merge_dicts({"a": 1}, {"a": 2}) == {"a": 2}


def test_merge_dicts_merges_nested_dicts(client):
    """Recursive merge must work; 0.3 crashed here on Python 3.10+."""
    result = client.merge_dicts({"a": {"x": 1}}, {"a": {"y": 2}})
    assert result == {"a": {"x": 1, "y": 2}}


def test_merge_dicts_merges_deeply_nested_dicts(client):
    result = client.merge_dicts(
        {"data": {"attributes": {"title": "t"}}},
        {"data": {"attributes": {"body": "b"}, "type": "node--article"}},
    )
    assert result == {
        "data": {"attributes": {"title": "t", "body": "b"}, "type": "node--article"}
    }


# --- get_taxonomy_term ------------------------------------------------------

def test_taxonomy_term_returns_existing_match(client):
    payload = {"data": {"attributes": {"name": "Thriller"}}}
    existing = make_response(json_body={"data": [{"id": "term-1"}]})

    with mock.patch("drupal_api.drupal.requests.get", return_value=existing):
        result = client.get_taxonomy_term("/jsonapi/taxonomy_term/genres", payload)

    assert result == {"id": "term-1"}


def test_taxonomy_term_creates_when_missing(client):
    payload = {"data": {"attributes": {"name": "Thriller"}}}
    missing = make_response(json_body={"data": []})
    created = make_response(json_body={"data": {"id": "term-new"}})

    with mock.patch("drupal_api.drupal.requests.get", return_value=missing), \
         mock.patch("drupal_api.drupal.requests.post", return_value=created):
        result = client.get_taxonomy_term("/jsonapi/taxonomy_term/genres", payload)

    assert result == {"id": "term-new"}


def test_taxonomy_term_filter_order_is_stable(client):
    """Query parameters must be an ordered sequence, not an unordered set."""
    payload = {"data": {"attributes": {"name": "Thriller"}}}
    existing = make_response(json_body={"data": [{"id": "term-1"}]})

    with mock.patch("drupal_api.drupal.requests.get", return_value=existing) as get:
        client.get_taxonomy_term("/jsonapi/taxonomy_term/genres", payload)

    params = get.call_args.kwargs["params"]
    assert isinstance(params, list)
    assert [key for key, _ in params] == [
        "filter[a-label][condition][path]",
        "filter[a-label][condition][operator]",
        "filter[a-label][condition][value]",
    ]


def test_taxonomy_term_default_extra_data_is_not_shared(client):
    """The default for extra data must not leak between calls."""
    import inspect

    signature = inspect.signature(client.get_taxonomy_term)
    default = signature.parameters["extra_data"].default
    assert default is None


# --- get_file_id ------------------------------------------------------------

def test_file_id_reuses_existing_file(client):
    existing = make_response(json_body={"data": [{"id": "file-1"}]})

    with mock.patch("drupal_api.drupal.requests.get", return_value=existing):
        result = client.get_file_id(
            "/jsonapi/media/image/field_media_image",
            file_url_or_path="/tmp/cover.png",
        )

    assert result == "file-1"


def test_file_id_uploads_local_file_when_missing(client, tmp_path):
    image = tmp_path / "cover.png"
    image.write_bytes(b"binary-content")

    missing = make_response(json_body={"data": []})
    uploaded = make_response(json_body={"data": {"id": "file-new"}})

    with mock.patch("drupal_api.drupal.requests.get", return_value=missing), \
         mock.patch("drupal_api.drupal.requests.post", return_value=uploaded) as post:
        result = client.get_file_id(
            "/jsonapi/media/image/field_media_image",
            file_url_or_path=str(image),
            local_file=True,
        )

    assert result == "file-new"
    assert post.call_args.kwargs["data"] == b"binary-content"
    assert 'filename="cover.png"' in post.call_args.kwargs["headers"]["Content-Disposition"]


def test_file_id_derives_filename_from_url(client):
    existing = make_response(json_body={"data": [{"id": "file-1"}]})

    with mock.patch("drupal_api.drupal.requests.get", return_value=existing) as get:
        client.get_file_id(
            "/jsonapi/media/image/field_media_image",
            file_url_or_path="https://cdn.invalid/covers/my-cover.jpg",
        )

    params = dict(get.call_args.kwargs["params"])
    assert params["filter[a-label][condition][value]"] == "my-cover.jpg"
