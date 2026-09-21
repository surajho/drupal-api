"""Necessary classes and modules"""
from drupal_api.drupal_entity import DrupalEntity


class DrupalNode(DrupalEntity):
    def __init__(
        self,
        title: str,
        node_type: str
    ):
        super().__init__()

        self.json_entity["data"]["type"] = node_type
        self.json_entity["data"]["attributes"] = {
            "title": title,
        }
