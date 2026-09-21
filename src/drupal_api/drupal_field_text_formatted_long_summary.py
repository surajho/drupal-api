"""Helper for Drupal's formatted long text field with summary."""
from __future__ import annotations

from typing import Any


class DrupalFieldTextFormattedLongSummary:
    """Builds the dict for a ``text_with_summary`` field.

    Parameters
    ----------
    value:
        Raw field value.
    output_format:
        Text format machine name. Defaults to ``basic_html``.
    processed:
        Pre-rendered output, omitted when None.
    summary:
        Field summary, omitted when None.
    """

    def __init__(
        self,
        value: str,
        output_format: str = "basic_html",
        processed: str | None = None,
        summary: str | None = None,
    ) -> None:
        self.field: dict[str, Any] = {"value": value, "format": output_format}

        if processed is not None:
            self.field["processed"] = processed

        if summary is not None:
            self.field["summary"] = summary
