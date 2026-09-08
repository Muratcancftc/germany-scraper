"""Server-Sent Events (SSE) helpers.

SSE is used instead of WebSocket because Vercel Functions are isolated per
request — a job runs inside the same streaming request that produced it, so
events travel over the request's own SSE stream. The frontend reads them with
`fetch` + ReadableStream.
"""

from __future__ import annotations

import json
from typing import Any


def sse_format(event: dict[str, Any]) -> str:
    """Serialize a single event dict into one SSE `data:` frame."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
