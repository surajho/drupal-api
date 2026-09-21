from drupal_api.drupal_entity import DrupalEntity


class DrupalParagraph(DrupalEntity):
    def __init__(
        self,
        type: str,
        parent_id: str,
        parent_type: str,
        parent_field_name: str
    ):
        super().__init__()

        self.json_entity["data"]["type"] = type
        self.json_entity["data"]["attributes"] = {
            "parent_id": parent_id,
            "parent_type": parent_type,
            "parent_field_name": parent_field_name
        }
