"""Base class for JSON:API entity payloads."""
from __future__ import annotations

from typing import Any


class DrupalEntity:
    """Holds the ``data`` envelope shared by every JSON:API entity.

    The ``id`` key is deliberately absent: JSON:API only accepts an ``id`` on
    creation when the client generates it, and sending ``null`` is invalid.
    Set ``json_entity["data"]["id"]`` explicitly when patching an entity.
    """

    def __init__(self) -> None:
        self.json_entity: dict[str, Any] = {"data": {"type": None}}
