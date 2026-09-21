from drupal_api.drupal_entity import DrupalEntity


class DrupalRedirect(DrupalEntity):
    def __init__(
        self,
        redirect_source: str,
        redirect_target: str,
        status_code: int = 301
    ):
        super().__init__()

        self.entity_url = "/jsonapi/redirect/redirect"

        self.json_entity["data"]["type"] = "redirect--redirect"
        self.json_entity["data"]["attributes"] = {
            "redirect_source": {
              "path": redirect_source
            },
            "redirect_redirect": {
              "uri": redirect_target
            },
            "status_code": status_code
        }
