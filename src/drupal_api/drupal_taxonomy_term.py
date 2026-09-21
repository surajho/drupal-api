"""Necessary classes and modules"""
from drupal_api.drupal_entity import DrupalEntity


class DrupalTaxonomyTerm(DrupalEntity):
    def __init__(
        self,
        name: str,
        entity_type: str
    ):
        super().__init__()

        self.json_entity["data"]["type"] = entity_type
        self.json_entity["data"]["attributes"] = {
            "name": name
        }
