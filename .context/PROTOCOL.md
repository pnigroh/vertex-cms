# LLM Session Protocol — Vertex CMS

## Purpose

This protocol ensures persistent context survives across LLM sessions. Every AI assistant working on this project MUST follow these rules.

---

## On Session Start (BEFORE writing any code)

1. **Read these files in order:**
   1. `llm-handoff.md` — orientation and current state
   2. `active-context.md` — what is being worked on right now
   3. `project-dna.md` — hard constraints and architecture decisions (skim if familiar)
   4. `decisions-log.md` — recent decisions (check last 3-5 entries)

2. **Verify understanding** — confirm you know:
   - What the current focus/sprint is
   - What bugs or blockers exist
   - What NOT to do (hard constraints)

3. **Do NOT start coding until you have read the above files.**

---

## During the Session

- **Before making an architecture decision**: check `project-dna.md` constraints and `decisions-log.md` for prior art.
- **When you make a decision**: append a new `DEC-NNN` entry to `decisions-log.md` immediately. Do not wait until the end.
- **When you discover a bug or blocker**: add it to `active-context.md` under "Potential Issues / Blockers".
- **When you complete a task**: update `active-context.md` to reflect the new state.

---

## On Session End (BEFORE closing)

1. **Update `active-context.md`:**
   - Move completed work from "Current Focus" to "What Was Just Done"
   - Add any new blockers or assumptions
   - Update the "Recent Changes" table with commits made this session

2. **Update `llm-handoff.md`:**
   - Revise "Current State" to reflect what is now working/not working
   - Update "What Likely Needs Doing Next" based on progress
   - Add any new "What NOT To Do" rules discovered during the session

3. **Append to `decisions-log.md`** for any decisions made but not yet logged.

4. **Update `project-dna.md`** ONLY if:
   - A new hard constraint was established
   - The stack changed (new dependency, version bump)
   - A new architecture decision was made

---

## File Ownership Rules

| File                | Who updates it    | How                          |
|---------------------|-------------------|------------------------------|
| `project-dna.md`    | Rarely            | Only for stack/constraint changes |
| `active-context.md` | Every session      | Read at start, write at end  |
| `decisions-log.md`  | When decisions happen | Append only, never edit/delete |
| `llm-handoff.md`    | Every session      | Rewrite "current state" section |
| `PROTOCOL.md`       | Rarely            | Only if the protocol itself needs updating |

---

## Formatting Rules

- `decisions-log.md` entries use the format: `## DEC-NNN: Title` with Date, Commit, Context, Decision, Alternatives, Consequences fields.
- `active-context.md` tables use `| col | col |` Markdown format.
- Dates use `YYYY-MM-DD` format.
- Commit references use the short hash (7 chars).
