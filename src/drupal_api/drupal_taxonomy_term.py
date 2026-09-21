"""JSON:API payload for a taxonomy term."""
from __future__ import annotations

from drupal_api.drupal_entity import DrupalEntity


class DrupalTaxonomyTerm(DrupalEntity):
    """A taxonomy term payload carrying a name.

    Parameters
    ----------
    name:
        Term name.
    entity_type:
        JSON:API resource type, e.g. ``taxonomy_term--tags``.
    """

    def __init__(self, name: str, entity_type: str) -> None:
        super().__init__()

        self.json_entity["data"]["type"] = entity_type
        self.json_entity["data"]["attributes"] = {"name": name}
