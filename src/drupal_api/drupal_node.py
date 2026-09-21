"""JSON:API payload for a node."""
from __future__ import annotations

from drupal_api.drupal_entity import DrupalEntity


class DrupalNode(DrupalEntity):
    """A node payload carrying a title.

    Parameters
    ----------
    title:
        Node title.
    node_type:
        JSON:API resource type, e.g. ``node--article``.
    """

    def __init__(self, title: str, node_type: str) -> None:
        super().__init__()

        self.json_entity["data"]["type"] = node_type
        self.json_entity["data"]["attributes"] = {"title": title}
