# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 7

"""MCP server that exposes the Practice Hub REST API to Claude Code.

Configuration comes from the environment:
    PRACTICE_API_URL    base URL of the hub (default: https://practice.fhsucyber.com)
    PRACTICE_API_TOKEN  your personal API token (required, never hard-coded)

Run with:  python server.py   (stdio transport, which is what `claude mcp add` expects)
"""

import json
import os
import ssl
import sys

import httpx
import truststore
from mcp.server.fastmcp import FastMCP

API_URL = os.environ.get("PRACTICE_API_URL", "https://practice.fhsucyber.com").rstrip("/")
API_TOKEN = os.environ.get("PRACTICE_API_TOKEN")
TIMEOUT = 15.0
# Verify HTTPS against the operating system's certificate store instead of certifi's bundle,
# so the server still works behind antivirus HTTPS scanning or a school/corporate proxy.
SSL_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

mcp = FastMCP("practice-hub")


def _error_message(resp: httpx.Response) -> str:
    """Turn a non-success API response into a short, readable message."""
    try:
        detail = resp.json().get("detail")
    except (ValueError, AttributeError):
        detail = None
    # 422 validation errors come back as a list of {"msg": ...} objects
    if isinstance(detail, list):
        detail = "; ".join(d.get("msg", str(d)) if isinstance(d, dict) else str(d) for d in detail)

    status = resp.status_code
    if status == 401:
        return ("Error 401 Unauthorized: the API token is missing or invalid. "
                "Check the PRACTICE_API_TOKEN environment variable.")
    if status == 403:
        return "Error 403 Forbidden: you can only edit or delete posts that you created."
    if status == 404:
        return "Error 404 Not Found: no post exists with that id."
    if status == 422:
        return f"Error 422 Invalid data: {detail or 'check the fields you sent.'}"
    return f"Error {status} from the Practice Hub API: {detail or resp.text[:200]}"


def _request(method: str, path: str, **kwargs) -> str:
    """Call the Practice Hub API and return either JSON text or a clear error message.

    This never raises, so a bad request can't crash the MCP server.
    """
    if not API_TOKEN:
        return ("Error: PRACTICE_API_TOKEN is not set. Set it in the environment "
                "(or pass it with `claude mcp add -e PRACTICE_API_TOKEN=...`) and restart the server.")
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        resp = httpx.request(method, f"{API_URL}{path}", headers=headers, timeout=TIMEOUT,
                             verify=SSL_CONTEXT, **kwargs)
    except httpx.HTTPError as exc:
        return f"Error: could not reach the Practice Hub at {API_URL} ({exc.__class__.__name__}: {exc})."

    if resp.is_error:
        return _error_message(resp)
    if resp.status_code == 204 or not resp.content:
        return "OK"
    try:
        return json.dumps(resp.json(), indent=2)
    except ValueError:
        return resp.text


@mcp.tool()
def list_posts(mine: bool = False, tag: str | None = None, author: str | None = None,
               limit: int | None = None, offset: int | None = None) -> str:
    """List posts on the Practice Hub.

    Use this to browse posts or to find the user's own posts.

    Args:
        mine: If True, return only posts written by the authenticated user ("my posts").
        tag: Optional tag to filter by (e.g. "python").
        author: Optional author username to filter by.
        limit: Optional maximum number of posts to return.
        offset: Optional number of posts to skip (for paging).

    Returns a JSON list of posts (each with id, title, body, tags, author, timestamps),
    or an error message.
    """
    params = {"mine": mine}
    if tag:
        params["tag"] = tag
    if author:
        params["author"] = author
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return _request("GET", "/api/v1/posts", params=params)


@mcp.tool()
def get_post(post_id: int) -> str:
    """Get a single Practice Hub post by its numeric id.

    Args:
        post_id: The id of the post to fetch.

    Returns the post as JSON, or an error message (e.g. 404 if it does not exist).
    """
    return _request("GET", f"/api/v1/posts/{post_id}")


@mcp.tool()
def create_post(title: str, body: str = "", tags: list[str] | None = None) -> str:
    """Create a new post on the Practice Hub as the authenticated user.

    Args:
        title: Post title (1-200 characters, required).
        body: Post body text (up to 20,000 characters).
        tags: Optional list of tag strings, e.g. ["mcp", "inf601"].

    Returns the newly created post as JSON (including its new id), or an error message.
    """
    payload = {"title": title, "body": body, "tags": tags or []}
    return _request("POST", "/api/v1/posts", json=payload)


@mcp.tool()
def update_post(post_id: int, title: str | None = None, body: str | None = None,
                tags: list[str] | None = None) -> str:
    """Edit one of the user's own Practice Hub posts.

    Only the fields you pass are changed; omitted fields are left as they are.
    The API only allows editing posts the user created (others return a 403 error).

    Args:
        post_id: The id of the post to edit.
        title: New title (optional).
        body: New body text (optional).
        tags: New full list of tags, replacing the old list (optional).

    Returns the updated post as JSON, or an error message.
    """
    payload = {}
    if title is not None:
        payload["title"] = title
    if body is not None:
        payload["body"] = body
    if tags is not None:
        payload["tags"] = tags
    if not payload:
        return "Error: nothing to update. Pass at least one of title, body, or tags."
    return _request("PATCH", f"/api/v1/posts/{post_id}", json=payload)


@mcp.tool()
def delete_post(post_id: int) -> str:
    """Permanently delete one of the user's own Practice Hub posts.

    The API only allows deleting posts the user created (others return a 403 error).
    This cannot be undone, so only call it when the user clearly asks to delete a post.

    Args:
        post_id: The id of the post to delete.

    Returns a confirmation message, or an error message.
    """
    result = _request("DELETE", f"/api/v1/posts/{post_id}")
    if result.startswith("Error"):
        return result
    return f"Post {post_id} was deleted."


if __name__ == "__main__":
    if not API_TOKEN:
        # stdout is reserved for the MCP protocol, so warnings go to stderr
        print("Warning: PRACTICE_API_TOKEN is not set; tools will return an error until it is.",
              file=sys.stderr)
    mcp.run()  # default transport is stdio
