---
name: todo
description: Track personal todo tasks — add, complete, and remove them through a simple single-page web app backed by SQLite. Use when the user wants a todo list, task tracker, or asks to start/open their todos. Triggers like "open my todos", "start the todo app", "track my tasks", "add a todo".
allowed-tools: Bash, Read
---

# todo

A tiny todo tracker: one Bun script ([`scripts/server.ts`](./scripts/server.ts)) that persists tasks in SQLite and serves a single-page app ([`scripts/index.html`](./scripts/index.html)) for adding, completing, and deleting them. No build step, no dependencies — Bun ships SQLite and an HTTP server.

## When to use

The user asks to list/open/start their todos, track tasks, or add/complete/remove a todo.

## Workflow

The CLI and the web app are two interfaces over the **same** SQLite DB — pick whichever fits the request. The DB is the source of truth; keep it stable across sessions (`DB=~/.todos.db`) so tasks persist.

1. **Start the server first — always.** Every other action (list, add, complete, remove, the web app) goes through the server's API, which owns the SQLite DB; nothing works until it's up. Check whether it's already running, and start it in the background only if it isn't (run from this skill's directory so the relative path resolves):
   ```bash
   curl -sf localhost:4321/api/todos >/dev/null 2>&1 \
     || DB=~/.todos.db PORT=4321 bun run scripts/server.ts &
   ```
   Give it a moment, then confirm `curl -sf localhost:4321/api/todos` succeeds before moving on. Only after this should you list/add/complete/remove.

2. **Default — no args: list current todos.** `/todo` with no arguments means "show me my list." List and present the open tasks in chat (id, title, priority, due date, overdue flag). Mention the web app URL for richer management.
   ```bash
   curl -s localhost:4321/api/todos    # returns all todos as JSON; done:0 are open, done:1 are completed
   ```

3. **Manage tasks from the CLI** when the user asks you to add/complete/remove directly:
   - Add: `curl -s -X POST localhost:4321/api/todos -H 'content-type: application/json' -d '{"title":"...","due":"2026-06-10","priority":"high"}'` — `due` (YYYY-MM-DD) and `priority` (`low`/`medium`/`high`) are optional.
   - Update (any of done/title/due/priority): `curl -s -X PATCH localhost:4321/api/todos/<id> -H 'content-type: application/json' -d '{"done":true}'`
   - Remove: `curl -s -X DELETE localhost:4321/api/todos/<id>`

4. **Open/start the app** when the user wants the UI: with the server up (Step 1), tell them to open `http://localhost:4321`. The SPA handles add / check-off / delete, shows priority and due-date badges, linkifies URLs, and has a collapsible **Completed** section.

## Notes

- **Persistence**: everything lives in the single SQLite file (`DB`). Back it up by copying that file.
- **Schema**: `todos(id, title, done, created, due, priority)` — created automatically on first run; older DBs are migrated (new columns added) on startup.
- Keep it simple. If you're tempted to add accounts, tags, or sync, ask the user first — this skill is intentionally minimal.
