"""Necessary classes and modules"""
from drupal_api.drupal_entity import DrupalEntity


class DrupalMediaImage(DrupalEntity):
    def __init__(
        self,
        image_detail: dict,
        image_uuid: str
    ):
        super().__init__()

        self.entity_url = "/jsonapi/media/image"

        self.json_entity["data"]["type"] = "media--image"
        self.json_entity["data"]["attributes"] = {
            "name": image_detail["name"],
        }

        self.json_entity["data"]["relationships"] = {
            "field_media_image": {
                "data": {
                    "type": "file--file",
                    "id": image_uuid,
                    "meta": {
                        "alt": image_detail["alt"],
                        "title": image_detail["title"],
                        "width": image_detail["width"],
                        "height": image_detail["height"]
                    }
                }
            }
        }
