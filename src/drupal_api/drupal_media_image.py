"""JSON:API payload for an image media entity."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from drupal_api.drupal_entity import DrupalEntity


class DrupalMediaImage(DrupalEntity):
    """An image media entity wrapping an already-uploaded file.

    Parameters
    ----------
    image_detail:
        Mapping with ``name``, ``alt``, ``title``, ``width`` and ``height``.
    image_uuid:
        UUID of the uploaded file to attach.
    """

    def __init__(self, image_detail: Mapping[str, Any], image_uuid: str) -> None:
        super().__init__()

        self.entity_url = "/jsonapi/media/image"

        self.json_entity["data"]["type"] = "media--image"
        self.json_entity["data"]["attributes"] = {"name": image_detail["name"]}

        self.json_entity["data"]["relationships"] = {
            "field_media_image": {
                "data": {
                    "type": "file--file",
                    "id": image_uuid,
                    "meta": {
                        "alt": image_detail["alt"],
                        "title": image_detail["title"],
                        "width": image_detail["width"],
                        "height": image_detail["height"],
                    },
                }
            }
        }
