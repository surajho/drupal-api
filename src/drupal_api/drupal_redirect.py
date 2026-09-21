"""JSON:API payload for a redirect."""
from __future__ import annotations

from drupal_api.drupal_entity import DrupalEntity


class DrupalRedirect(DrupalEntity):
    """A redirect from one path to another.

    Parameters
    ----------
    redirect_source:
        Source path, without a leading slash in Drupal's own convention.
    redirect_target:
        Target URI, e.g. ``internal:/node/1`` or an absolute URL.
    status_code:
        HTTP status to serve. Defaults to 301.
    """

    def __init__(
        self,
        redirect_source: str,
        redirect_target: str,
        status_code: int = 301,
    ) -> None:
        super().__init__()

        self.entity_url = "/jsonapi/redirect/redirect"

        self.json_entity["data"]["type"] = "redirect--redirect"
        self.json_entity["data"]["attributes"] = {
            "redirect_source": {"path": redirect_source},
            "redirect_redirect": {"uri": redirect_target},
            "status_code": status_code,
        }
