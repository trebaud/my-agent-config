#!/usr/bin/env bun
// Todo app: SQLite persistence + single-page UI, all served by one Bun process.
// Usage: bun run server.ts            (DB at ./todos.db, port 4321)
//        DB=/path/todos.db PORT=8080 bun run server.ts

import { Database } from "bun:sqlite";
import { file } from "bun";

const DB_PATH = process.env.DB ?? "./todos.db";
const PORT = Number(process.env.PORT ?? 4321);

const db = new Database(DB_PATH);
db.run(`CREATE TABLE IF NOT EXISTS todos (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  title     TEXT NOT NULL,
  done      INTEGER NOT NULL DEFAULT 0,
  created   TEXT NOT NULL DEFAULT (datetime('now')),
  due       TEXT,
  priority  TEXT
)`);

// Migrate older DBs that predate the due/priority columns.
const cols = new Set(
  db.query<{ name: string }, []>("PRAGMA table_info(todos)").all().map(c => c.name),
);
if (!cols.has("due")) db.run("ALTER TABLE todos ADD COLUMN due TEXT");
if (!cols.has("priority")) db.run("ALTER TABLE todos ADD COLUMN priority TEXT");

const PRIORITIES = new Set(["low", "medium", "high"]);
const clean = (v: unknown) => (typeof v === "string" && v.trim() ? v.trim() : null);

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });

const indexHtml = new URL("./index.html", import.meta.url).pathname;

Bun.serve({
  port: PORT,
  async fetch(req) {
    const { pathname } = new URL(req.url);
    const m = pathname.match(/^\/api\/todos\/(\d+)$/);
    const id = m ? Number(m[1]) : null;

    // --- API ---
    if (pathname === "/api/todos" && req.method === "GET") {
      // Open tasks first; within each group, soonest due date wins (no-due last),
      // then higher priority, then newest.
      return json(
        db
          .query(
            `SELECT * FROM todos ORDER BY done ASC,
               (due IS NULL) ASC, due ASC,
               CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 WHEN 'low' THEN 2 ELSE 3 END ASC,
               id DESC`,
          )
          .all(),
      );
    }
    if (pathname === "/api/todos" && req.method === "POST") {
      const { title, due, priority } = await req.json();
      if (!title?.trim()) return json({ error: "title required" }, 400);
      const p = clean(priority);
      const row = db
        .query("INSERT INTO todos (title, due, priority) VALUES (?, ?, ?) RETURNING *")
        .get(title.trim(), clean(due), p && PRIORITIES.has(p) ? p : null);
      return json(row, 201);
    }
    if (id !== null && req.method === "PATCH") {
      const body = await req.json();
      const sets: string[] = [];
      const args: (string | number | null)[] = [];
      if ("done" in body) { sets.push("done = ?"); args.push(body.done ? 1 : 0); }
      if ("title" in body && body.title?.trim()) { sets.push("title = ?"); args.push(body.title.trim()); }
      if ("due" in body) { sets.push("due = ?"); args.push(clean(body.due)); }
      if ("priority" in body) {
        const p = clean(body.priority);
        sets.push("priority = ?"); args.push(p && PRIORITIES.has(p) ? p : null);
      }
      if (!sets.length) return json({ error: "nothing to update" }, 400);
      args.push(id);
      const row = db
        .query(`UPDATE todos SET ${sets.join(", ")} WHERE id = ? RETURNING *`)
        .get(...args);
      return row ? json(row) : json({ error: "not found" }, 404);
    }
    if (id !== null && req.method === "DELETE") {
      db.run("DELETE FROM todos WHERE id = ?", [id]);
      return json({ ok: true });
    }

    // --- SPA ---
    if (pathname === "/" || pathname === "/index.html") {
      return new Response(file(indexHtml), {
        headers: { "content-type": "text/html" },
      });
    }
    return new Response("Not found", { status: 404 });
  },
});

console.log(`Todo app on http://localhost:${PORT}  (db: ${DB_PATH})`);
