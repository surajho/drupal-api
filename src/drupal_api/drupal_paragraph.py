"""JSON:API payload for a paragraph."""
from __future__ import annotations

from drupal_api.drupal_entity import DrupalEntity


class DrupalParagraph(DrupalEntity):
    """A paragraph payload bound to its parent entity.

    Parameters
    ----------
    paragraph_type:
        JSON:API resource type, e.g. ``paragraph--text``.
    parent_id:
        ID of the entity this paragraph belongs to.
    parent_type:
        Entity type of the parent, e.g. ``node``.
    parent_field_name:
        Field on the parent that references this paragraph.
    """

    def __init__(
        self,
        paragraph_type: str,
        parent_id: str,
        parent_type: str,
        parent_field_name: str,
    ) -> None:
        super().__init__()

        self.json_entity["data"]["type"] = paragraph_type
        self.json_entity["data"]["attributes"] = {
            "parent_id": parent_id,
            "parent_type": parent_type,
            "parent_field_name": parent_field_name,
        }
