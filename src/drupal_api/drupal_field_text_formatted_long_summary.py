class DrupalFieldTextFormattedLongSummary:
    def __init__(
        self,
        value: str,
        output_format: str = "basic_html",
        processed: str = None,
        summary: str = None
    ):
        self.field = {
            "value": value,
            "format": output_format
        }

        if processed is not None:
            self.field["processed"] = processed

        if summary is not None:
            self.field["summary"] = summary
