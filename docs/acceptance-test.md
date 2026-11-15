# Acceptance test transcript

I ran this test on 2026-11-14 with Claude Code (Claude Opus 5.5) and the `practice-hub` server registered by `claude mcp add`. Claude Code ran headless (`claude -p ... --output-format stream-json`) and could only use the four `mcp__practice-hub__*` tools. Below are the real tool calls and results from that recorded session.

**MCP server status at startup:** `practice-hub` is `connected`.

## Prompt

> Using the practice-hub MCP server, do the following in order and report each result: (1) list my posts; (2) create a new post titled "Hello from my MCP server" with body "Created by Claude Code through my Mini Project 7 server." and tags mcp and inf601; (3) update that new post so its body says "Edited by Claude Code through my Mini Project 7 MCP server." and add the tag edited; (4) get the post again to confirm the change; (5) try to get post id 99999999 to show how a missing post is handled.

## Tool calls

### 1. `list_posts`

Arguments:
```json
{
  "mine": true
}
```
Result:
```
[
  {
    "id": 8,
    "title": "Week 3 lab",
    "body": "This is Alex Crenshaw and I have successfully finished Mini Project 1 for INF 601",
    "tags": [],
    "author_id": 13,
    "author_name": "Alex Crenshaw",
    "created_at": "2026-09-03T21:23:20.053405",
    "updated_at": "2026-09-03T21:23:20.053415",
    "attachments": []
  }
]
```

### 2. `create_post`

Arguments:
```json
{
  "title": "Hello from my MCP server",
  "body": "Created by Claude Code through my Mini Project 7 server.",
  "tags": [
    "mcp",
    "inf601"
  ]
}
```
Result:
```
{
  "id": 62,
  "title": "Hello from my MCP server",
  "body": "Created by Claude Code through my Mini Project 7 server.",
  "tags": [
    "mcp",
    "inf601"
  ],
  "author_id": 13,
  "author_name": "Alex Crenshaw",
  "created_at": "2026-11-15T04:56:26.025465",
  "updated_at": "2026-11-15T04:56:26.025475",
  "attachments": []
}
```

### 3. `update_post`

Arguments:
```json
{
  "post_id": 62,
  "body": "Edited by Claude Code through my Mini Project 7 MCP server.",
  "tags": [
    "mcp",
    "inf601",
    "edited"
  ]
}
```
Result:
```
{
  "id": 62,
  "title": "Hello from my MCP server",
  "body": "Edited by Claude Code through my Mini Project 7 MCP server.",
  "tags": [
    "mcp",
    "inf601",
    "edited"
  ],
  "author_id": 13,
  "author_name": "Alex Crenshaw",
  "created_at": "2026-11-15T04:56:26.025465",
  "updated_at": "2026-11-15T04:56:30.176440",
  "attachments": []
}
```

### 4. `get_post`

Arguments:
```json
{
  "post_id": 62
}
```
Result:
```
{
  "id": 62,
  "title": "Hello from my MCP server",
  "body": "Edited by Claude Code through my Mini Project 7 MCP server.",
  "tags": [
    "mcp",
    "inf601",
    "edited"
  ],
  "author_id": 13,
  "author_name": "Alex Crenshaw",
  "created_at": "2026-11-15T04:56:26.025465",
  "updated_at": "2026-11-15T04:56:30.176440",
  "attachments": []
}
```

### 5. `get_post`

Arguments:
```json
{
  "post_id": 99999999
}
```
Result:
```
Error 404 Not Found: no post exists with that id.
```

## Claude's final answer

All five steps worked as expected, including the error case at the end.

**(1) List my posts:** You had one post before this run.
| id | title | body | tags |
|---|---|---|---|
| 8 | Week 3 lab | "This is Alex Crenshaw and I have successfully finished Mini Project 1 for INF 601" | none |

**(2) Create a post:** The new post got **id 62**.
- Title: "Hello from my MCP server"
- Body: "Created by Claude Code through my Mini Project 7 server."
- Tags: `mcp`, `inf601`
- Created at: 2026-11-15T04:56:26

**(3) Update post 62:**
- Body is now: "Edited by Claude Code through my Mini Project 7 MCP server."
- Tags are now: `mcp`, `inf601`, `edited`. The update tool replaces the whole tag list, so I sent all three tags to keep the first two.
- `updated_at` changed to 2026-11-15T04:56:30. The title and `created_at` didn't change.

**(4) Get post 62 again:** It returned the new body and all three tags, so the edit was saved on the server.

**(5) Get post 99999999:** The server returned:
```
Error 404 Not Found: no post exists with that id.
```
Your error handling turns the API's 404 into a plain message instead of crashing.

Post 62 is still on the Practice Hub. Let me know if you want me to delete it.

## Extra error-handling check (403 / 404 / 422)

I also called the tool functions directly from Python. For the 403 case, the
update set another student's post title to the title it already had, so the
post could not change even if the API accepted the request.

```
>>> update_post(63, title=<its current title>)   # post 63 belongs to another student
Error 403 Forbidden: you can only edit or delete posts that you created.
>>> delete_post(99999999)
Error 404 Not Found: no post exists with that id.
>>> create_post(title="")
Error 422 Invalid data: String should have at least 1 character
```

The server returned a message for each case and kept running.
