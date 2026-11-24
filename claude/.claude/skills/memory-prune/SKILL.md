---
name: memory-prune
description: Prune and verify the project's auto memory after something landed - when the Stop hook says "memory-prune due", when the user says "save context", "save session", "prune memory", "wrap up", or before ending a session in which main moved. Deletes or re-dates stale memories and shrinks MEMORY.md; never appends a session ledger.
---

# Memory prune

Auto memory adds and rarely removes. This skill is the removal pass: it makes the
memory directory *smaller and truer* at the end of a piece of work. It never writes a
"what happened this session" ledger, because git already holds that.

The memory directory for the current project is named in the system prompt. `MEMORY.md`
there is the index, loaded every session; the other files are leaves, loaded on demand.

## The one test

For every line you touch: **would it be wrong tomorrow without anyone editing it?** Then it
is a lookup git or the tree answers, not a memory. Delete it. Commit SHAs, PR numbers,
branch lists, worktree inventories, directory trees, dependency lists and test counts all
fail this test. What passes: a ruling and its date, a decision and its why, a trap that
cost a session, where an external thing lives.

## Steps

### 1. What moved

```bash
git log --oneline <tip-memory-claims>..<default-branch>
git branch -a --list; git worktree list
```

Done when: you can name every fact in `MEMORY.md`'s current-state section that these
commits contradict (a tip, a branch that is gone, a PR now merged, a follow-up now Done).

### 2. Verify the leaves the work touched

Open every leaf file whose subject the session's work touched (the index line says what
each holds). For each claim that names a path, command, flag, class, ticket or setting,
check it still exists or still holds. Re-date what is still true and changed; delete
what is false; never leave a wrong claim with a caveat beside it.

Done when: each opened leaf carries only claims you checked this session or that do not
depend on the tree.

### 3. Shrink the index

In `MEMORY.md`:
- Replace the current-state section with the tip, the open branches by purpose (not by
  name if a name will change), the guards in force, and the open work. Facts with a
  date keep it, absolute (`2026-09-16`), never relative.
- Move anything ledger-shaped (what each PR landed, a chronology, a list of ids) into
  a dated leaf and leave a one-line index entry pointing at it.
- Drop sections that cache the environment (a stack list, a key-paths list, a layout).
- Keep one line per memory in the index, each saying enough to decide whether to open
  the leaf. Update the lines whose leaves changed.

Done when: `wc -l MEMORY.md` is no larger than before, well under the 200-line load
limit, and no line fails the test above.

### 4. Prune the friction log

`~/.claude/friction-log.md` is shared by every project. Read it whole (it is under 60
lines). Delete an entry whose cause is gone for good: the fix was committed to the repo
it names, the tool was upgraded past it, the service changed. Merge entries with the same
symptom into one line carrying the earliest date. Keep the symptom's wording. Never add
an entry here; entries are added at the moment the time is lost.

Done when: no entry describes a cause that no longer exists, and the file is under 60
lines.

### 5. Report

Tell the user in a few lines: what was deleted, what was re-dated, the index size before
and after. Nothing else; the point of the skill is that it leaves less behind, not more.

## Not this skill's job

- Recording what the session did: that is git, the PR body, and the ticket comment.
- Adding memories: auto memory does that during the session, with the same test.
- Restoring context: the SessionStart hook prints git's facts at launch; `--resume`
  restores a conversation.
