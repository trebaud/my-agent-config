#!/usr/bin/env bun
// Validates a .marmite/prd.json produced by `marmite to-prd`.
//
// Stricter than the runtime schema in src/core/prd.ts: we want bad PRDs caught
// here, before `marmite cook` runs and the user has invested time. The runtime
// loader stays permissive so older PRDs still load; this script enforces what a
// freshly-generated PRD should look like.
//
// Usage: bun run validate-prd.ts <path-to-prd.json>
// Exits 0 on success, 1 with a numbered error list on failure.

import { existsSync, readFileSync } from "fs";
import { z } from "zod";

const StorySchema = z.object({
  id: z.string().regex(/^US-\d{3,}$/, "id must match US-### (e.g. US-001)"),
  title: z.string().min(1, "title must be non-empty"),
  description: z.string().min(1, "description must be non-empty"),
  acceptanceCriteria: z.array(z.string().min(1)).min(1, "acceptanceCriteria must contain at least one item"),
  priority: z.number().int().nonnegative(),
  passes: z.boolean(),
  notes: z.string().optional(),
  dependencies: z.array(z.string()).optional(),
  epic: z.string().min(1),
});

const PrdSchema = z.object({
  project: z.string().min(1, "project must be non-empty"),
  description: z.string().min(1, "description must be non-empty"),
  userStories: z.array(StorySchema).min(1, "userStories must contain at least one story"),
});

function fail(errors: string[]): never {
  console.error(`\x1b[31m✗ prd.json validation failed:\x1b[0m`);
  errors.forEach((e, i) => console.error(`  ${i + 1}. ${e}`));
  process.exit(1);
}

function main(): void {
  const path = process.argv[2];
  if (!path) {
    console.error("Usage: bun run validate-prd.ts <path-to-prd.json>");
    process.exit(2);
  }
  if (!existsSync(path)) fail([`file not found: ${path}`]);

  let raw: unknown;
  try {
    raw = JSON.parse(readFileSync(path, "utf8"));
  } catch (err) {
    fail([`invalid JSON: ${err instanceof Error ? err.message : String(err)}`]);
  }

  const parsed = PrdSchema.safeParse(raw);
  if (!parsed.success) {
    const errors = parsed.error.issues.map((i) => `${i.path.join(".") || "<root>"}: ${i.message}`);
    fail(errors);
  }

  const stories = parsed.data.userStories;
  const semanticErrors: string[] = [];

  // Duplicate IDs.
  const seen = new Map<string, number>();
  for (const [idx, s] of stories.entries()) {
    const prev = seen.get(s.id);
    if (prev !== undefined) {
      semanticErrors.push(`duplicate story id "${s.id}" at indexes ${prev} and ${idx}`);
    } else {
      seen.set(s.id, idx);
    }
  }

  // Dependency references must resolve and must point at lower-priority stories.
  for (const s of stories) {
    for (const dep of s.dependencies ?? []) {
      const depIdx = seen.get(dep);
      if (depIdx === undefined) {
        semanticErrors.push(`story ${s.id}: dependency "${dep}" does not exist`);
        continue;
      }
      const depStory = stories[depIdx]!;
      if (depStory.priority >= s.priority) {
        semanticErrors.push(
          `story ${s.id} (priority ${s.priority}) depends on ${dep} (priority ${depStory.priority}) — dependencies must have lower priority`,
        );
      }
    }
  }

  // All freshly-generated stories should start with passes: false.
  for (const s of stories) {
    if (s.passes !== false) {
      semanticErrors.push(`story ${s.id}: passes must be false in a freshly-generated prd.json (got ${s.passes})`);
    }
  }

  if (semanticErrors.length > 0) fail(semanticErrors);

  console.log(`\x1b[32m✓ prd.json valid\x1b[0m (${stories.length} stories)`);
}

main();
