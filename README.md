# drupal-api

A small Python client for the [Drupal JSON:API](https://www.drupal.org/docs/core-modules-and-themes/core-modules/jsonapi-module),
covering the entity operations you need to push content into a Drupal site:
nodes, taxonomy terms, media images, paragraphs, redirects and file uploads.

## Install

```bash
pip install drupal-api
```

Requires Python 3.10 or newer.

## Usage

```python
from drupal_api import Drupal, DrupalAPIError, DrupalNode

client = Drupal("https://example.com", "prod", "username", "password")

try:
    response = client.get_entities(
        "/jsonapi/node/article",
        parameters=[
            ("filter[a-label][condition][path]", "title"),
            ("filter[a-label][condition][operator]", "="),
            ("filter[a-label][condition][value]", "Hello world"),
        ],
    )
except DrupalAPIError as error:
    print(error.status_code, error.body)
else:
    articles = response.json()["data"]
```

Pass query filters as a **list of two-tuples** so their order stays stable.

### Creating an entity

```python
node = DrupalNode("Hello world", "node--article")
client.post_entity("/jsonapi/node/article", node.json_entity)
```

### Fetching a whole collection

`get_drupal_entity_collection` follows JSON:API `next` links until the
collection is exhausted, and always returns a list:

```python
for article in client.get_drupal_entity_collection("/jsonapi/node/article"):
    print(article["id"])
```

### Uploading a file

```python
file_uuid = client.get_file_id(
    "/jsonapi/media/image/field_media_image",
    file_url_or_path="/path/to/cover.jpg",
    local_file=True,
)
```

Reuses an existing file with the same name when one is present, and uploads it
otherwise.

## Error handling

Every failing request raises `DrupalAPIError`:

```python
except DrupalAPIError as error:
    error.status_code  # 403
    error.url          # the requested URL
    error.body         # parsed JSON errors, or truncated text for HTML bodies
    error.response     # the underlying requests.Response
```

Upgrading from 0.3? The library used to call `sys.exit(0)` on failure, which
terminated your process and reported success. See [CHANGELOG.md](CHANGELOG.md)
for the full migration notes.

## Configuration

| Argument | Purpose |
| --- | --- |
| `domain` | Base URL of the site, e.g. `https://example.com` |
| `environment` | `prod` verifies TLS; `dev` disables it for self-signed certificates |
| `username`, `password` | HTTP basic auth credentials |
| `timeout` | Seconds before a request is abandoned (default 30) |

## Logging

The library logs through `logging.getLogger("drupal_api")` and never prints:

```python
import logging
logging.getLogger("drupal_api").setLevel(logging.INFO)
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy
```
