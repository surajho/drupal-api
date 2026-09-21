# Changelog

All notable changes to this project are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-09-21

First stable release. It contains breaking changes; read the migration notes
below before upgrading from 0.3.

### Breaking

- **Errors raise instead of terminating the process.** Every failing request
  used to call `sys.exit(0)`, which killed the caller and reported *success*
  to the shell — a failed import looked like a clean run to cron and CI.
  Failures now raise `DrupalAPIError`, carrying `status_code`, `url`, `body`
  and the originating `response`.
- **An unknown `environment` raises `ValueError`** rather than `SystemExit`.
- **`DrupalEntity` no longer emits `"id": None`.** JSON:API does not accept a
  null `id` on creation. Set `json_entity["data"]["id"]` explicitly when
  patching an existing entity.
- **`bson` is no longer used.** 0.3 imported `bson.json_util` without
  declaring the dependency, so a clean install failed on `import`. Dates are
  now serialised to ISO-8601 by a built-in default, which is what Drupal
  expects; 0.3 emitted BSON extended JSON (`{"$date": ...}`) for datetimes.
- **Renamed parameters** to follow PEP 8: `get_taxonomy_term(postUrl, data,
  extraData)` is now `get_taxonomy_term(post_url, data, extra_data)`, and
  `DrupalParagraph(type, ...)` is now `DrupalParagraph(paragraph_type, ...)`.
  Positional callers are unaffected.
- **`get_drupal_entity_collection` returns `[]`** for an empty collection
  instead of `{}`, so the return type is always a list.
- **Python 3.10 or newer is required.** 3.9 reached end of life in October
  2025, and the recursive merge below cannot work on it as written.
- Non-HTTP(S) URLs are rejected when downloading a file.

### Fixed

- **`merge_dicts` crashed on Python 3.10+.** It referenced
  `collections.Mapping`, removed in 3.10, so any merge involving a nested
  dictionary raised `AttributeError`. This made `get_taxonomy_term(...,
  extra_data=...)` unusable. It now uses `collections.abc.Mapping`.
- **Every request now sends a timeout** (default 30s, configurable via the
  `timeout` constructor argument). Previously a hung server blocked forever.
- **Error reporting no longer masks the error.** The old handler called
  `response.json()` on a failed response, so an HTML 502 or an empty body
  raised `JSONDecodeError` and hid the real HTTP error. Non-JSON bodies are
  now captured as truncated text.
- **Query filters are ordered.** Filter parameters were built as `set`s, so
  the generated query string varied between runs.
- The undeclared `bson`/`pymongo` dependency is gone; `requests` and
  `fake-useragent` are the only runtime requirements.

### Added

- `DrupalAPIError` for all API failures.
- `py.typed` marker, so type hints reach consumers' type checkers.
- Logging via `logging.getLogger("drupal_api")` in place of `print`; the
  library no longer writes to stdout.
- A test suite, plus ruff and mypy configuration.
- Public re-exports from `drupal_api`, so `from drupal_api import Drupal`
  works instead of reaching into submodules.
- Project metadata: repository URL, classifiers and `requires-python`.

### Note

- No licence is declared yet. PyPI shows 0.3 as unlicensed; pick one and add
  a `LICENSE` file plus `license` metadata before the next publish.

## [0.3] - 2023-10-06

Initial published release.
