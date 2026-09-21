"""JSON:API payload builders."""
from __future__ import annotations

from drupal_api.drupal_entity import DrupalEntity
from drupal_api.drupal_media_image import DrupalMediaImage
from drupal_api.drupal_node import DrupalNode
from drupal_api.drupal_paragraph import DrupalParagraph
from drupal_api.drupal_redirect import DrupalRedirect
from drupal_api.drupal_taxonomy_term import DrupalTaxonomyTerm
from drupal_api.drupal_field_text_formatted_long_summary import (
    DrupalFieldTextFormattedLongSummary,
)


def test_node_payload():
    node = DrupalNode("Title", "node--article")
    assert node.json_entity["data"]["type"] == "node--article"
    assert node.json_entity["data"]["attributes"] == {"title": "Title"}


def test_taxonomy_term_payload():
    term = DrupalTaxonomyTerm("Thriller", "taxonomy_term--genres")
    assert term.json_entity["data"]["type"] == "taxonomy_term--genres"
    assert term.json_entity["data"]["attributes"] == {"name": "Thriller"}


def test_media_image_payload():
    media = DrupalMediaImage(
        {"name": "n", "alt": "a", "title": "t", "width": 10, "height": 20}, "file-uuid"
    )
    relationship = media.json_entity["data"]["relationships"]["field_media_image"]["data"]
    assert media.entity_url == "/jsonapi/media/image"
    assert relationship["id"] == "file-uuid"
    assert relationship["meta"]["width"] == 10


def test_paragraph_payload():
    paragraph = DrupalParagraph("paragraph--text", "parent-1", "node", "field_body")
    assert paragraph.json_entity["data"]["type"] == "paragraph--text"
    assert paragraph.json_entity["data"]["attributes"]["parent_id"] == "parent-1"


def test_redirect_payload_defaults_to_301():
    redirect = DrupalRedirect("/old", "internal:/new")
    attributes = redirect.json_entity["data"]["attributes"]
    assert attributes["status_code"] == 301
    assert attributes["redirect_source"] == {"path": "/old"}


def test_formatted_long_summary_omits_unset_optionals():
    field = DrupalFieldTextFormattedLongSummary("body text")
    assert field.field == {"value": "body text", "format": "basic_html"}


def test_formatted_long_summary_includes_set_optionals():
    field = DrupalFieldTextFormattedLongSummary("v", summary="s", processed="p")
    assert field.field["summary"] == "s"
    assert field.field["processed"] == "p"


def test_entity_does_not_emit_a_null_id():
    """JSON:API forbids a null id on creation; it should be absent."""
    assert "id" not in DrupalEntity().json_entity["data"]
