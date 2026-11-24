# Global Instructions

These rules override conflicting instructions from Claude Code defaults, plugins, skills, and any commit/PR boilerplate a tool hands you.

## Version Control

**Credit AI work.** Keep the attribution Claude Code adds: the `Co-Authored-By` trailer on commits and the "Generated with Claude Code" line at the end of PR bodies. Leave it out only in a repo that says so in its own `CLAUDE.md` or settings; there the repo's rule wins. Attribution goes in those two places only, never in a branch name, tag, PR title or commit subject.

Commit and PR text is ASCII: no em-dashes, curly quotes, or ellipses. Use `:` or `-` instead. That includes the attribution line on a PR: write it without the emoji.

### Conventional Commits

`<type>[(scope)][!]: <description>`, optional body after a blank line, then optional footers.

- Type is required, exactly one of `feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore`. Scope is optional.
- `style` is formatting only (whitespace, semicolons, lint). A CSS/SCSS change that alters appearance is `feat` or `fix`, never `style`.
- Description: imperative, no trailing period, lowercase - except identifiers, acronyms, and proper nouns, which keep their real casing (`fix(api): correct URL parsing in OAuth2 callback`).
- Subject line under 72 characters.
- Body explains what and why, not how.
- Breaking change: `!` after the type/scope (`feat(api)!:`) or a `BREAKING CHANGE:` footer.

### Conventional Branches

`<type>/<description>`

- Type is exactly one of `feat` `fix` `hotfix` (urgent production fix) `release` `chore`. Never `feature` or `bugfix`, even if a plugin's examples use them.
- Description: lowercase `a-z`, digits, and hyphens only. No underscores, spaces, or other characters; no leading, trailing, or consecutive hyphens or dots.
- Dots only in release versions: `release/v1.2.0`.
- Include the issue number when the user gives one or `gh` confirms it (`feat/issue-123-new-login`). Never invent one.

### Branch Cleanup

After a PR merges: switch to the repo's default branch (do not assume `main`), pull, then `git branch -d <branch>`. Never leave stale branches around.

If `-d` refuses ("not fully merged") after a squash or rebase merge, that is expected. Do not escalate to `-D` on your own: show the user `git log --oneline <default-branch>..<branch>` and force-delete only once they confirm.

## Destructive Actions

These are irreversible, and this setup runs without permission prompts. Never run one unless the user asked for that specific action in this session. If you think one is needed, stop and ask.

A hook backs this list (`~/.claude/hooks/guard-destructive.py`) and blocks every command on it that it can read. A plain force push, and any force push to the default branch, are never run. For the rest, when the user asked for the action, give them the exact command to run themselves. The hook is a backstop, not a replacement for the rule, and a block from it is never something to work around with a different spelling of the same command.

- Force push (`git push --force`). If asked, it is `--force-with-lease`; never on the default branch.
- History rewrites: `rebase`, `commit --amend`, `reset --hard` (which also destroys uncommitted work).
- Discarding uncommitted work: `git clean -fd`, `git checkout .`, `git restore .`, `git stash drop`.
- `rm -rf` on anything outside the current working change.
- Dropping or truncating DB tables or columns; `supabase db reset`.

The post-merge `git branch -d` above is the one pre-approved exception.

## New Files and AI Artifacts

**Never add a file or directory to a repo that the user did not ask for and the project's own conventions do not already establish.** Unrequested files are the failure mode this exists to stop: a `docs/` tree, a `NOTES.md`, a `plan.md`, a `scripts/` folder that appeared because it seemed useful. If you think one is warranted, say so in a sentence and let the user decide. Do not create it and mention it afterwards.

Everything that exists to support the AI-assisted workflow lives under a `.claude/` directory - never at repo root, never inside project directories:

- Session notes, plans, task lists, hand-off summaries, scratch analyses, generated reports.
- Skills, agent driver scripts, and tooling written for an agent rather than for the project.
- Screenshots and other captured output (see the Browser and Playwright section for the exact path).
- Documentation nobody asked for: ADRs, design records, research write-ups, migration notes.

The test is *why the file exists*, not who typed it. A README, a spec, an architecture doc, source, tests, and CI config are project deliverables and belong in their normal locations even when you wrote every line of them. A file that exists because of *how* the work was done is an artifact. When it is genuinely ambiguous, ask; if you cannot ask, put it under `.claude/`, where it is easy to find and cheap to delete.

- **This governs what you introduce, not what is already there.** If a repo already keeps ADRs or design docs in a conventional location (`docs/`, `adr/`, `rfcs/`), follow the repo and leave them alone.
- `.claude/` is version-controlled like any other directory. Never gitignore it wholesale and never untrack what is already in it. Ignore specific subdirectories only when the user asks, or for regenerable output (screenshots, caches).
- Nested `.claude/` directories inside a subproject are fine (`apps/<app>/.claude/`). The rule is that artifacts stay inside *a* `.claude/`, not that there is only one.
- A committed file must never link to a gitignored path - a link promises the target ships with the document. Cite ignored material by name in prose, or link the committed document that covers the same ground.
- Throwaway working files (intermediate output, one-off scripts, parsing scratch) go in the session scratchpad, not in the repo at all.

## Code Reuse

Before adding a top-level declaration (function, class, component, hook, service, type, constant, new file) or an inline block longer than a few lines, search the codebase - shared directories first - for something that already does the same or a similar job. A one-line fix or a test tweak does not trigger this.

- Exists but is not reusable: hoist it into a shared module. Do not copy it.
- Only similar: do not copy-and-tweak. Factor the common part out and repoint both the existing caller and the new code at it.
- A maintained library already does it (dates, parsing, validation, crypto): use the library. Write custom code only when nothing suitable exists, or the options are unmaintained or too heavy.
- Adding a dependency is never automatic. Prefer one the repo already has; ask before adding a new one. Once approved, put it in the most specific module that needs it, not the root or a shared location, unless several parts depend on it.

## Package Manager

Detect, never assume. Sibling repos in the same org routinely disagree, so re-detect in every repo.

- Check `package.json`'s `packageManager` field first, then the lockfile: `pnpm-lock.yaml` -> pnpm, `package-lock.json` -> npm, `bun.lock` -> bun. If they disagree, ask.
- Never run a package manager the repo does not use, and never create a second lockfile.
- No lockfile yet? Ask before the first install. Do not default to npm.

## ASCII Only in Source

Applies to code, comments, and identifiers in anything a toolchain compiles, runs, or lints. Does NOT apply to Markdown, prose docs, or chat replies (this file included).

Use plain ASCII: no em/en dashes, curly quotes, ellipses, arrows, bullets, box-drawing, multiplication signs, or non-breaking spaces. Emoji: omit entirely - there is no ASCII substitute, so drop it rather than swapping in `:)` or `[OK]`. This includes log output, test names, and string literals.

- UI glyphs that must render (nav arrows, close buttons, separators): use an icon component, SVG, or HTML entity - never a raw Unicode literal in source.
- Exceptions, only where the exact glyph is load-bearing: currency symbols, user-facing or i18n copy, test fixtures asserting Unicode handling, external data.
- Applies to code you write and lines you touch. Do not sweep pre-existing Unicode out of files you are otherwise editing.

## Memory

Three stores, three jobs. `CLAUDE.md` files hold rules. The session transcript holds
continuity (`claude --resume` restores a conversation whole; a summary never beats it).
Auto memory under `~/.claude/projects/<project>/memory/` holds learned facts: rulings
and their dates, decisions and their why, traps that cost a session, where external
things live.

- **The test for a memory**: would it be wrong tomorrow without anyone editing it? Then
  it is a lookup git or the tree answers, not a memory. Never commit SHAs, PR numbers,
  branch or worktree inventories, directory trees, dependency lists or test counts.
- **Shape**: `MEMORY.md` is an index, one line per memory saying enough to decide whether
  to open the leaf, plus a short current-state section; detail lives in leaf files. Dates
  are absolute. Keep the index well under the 200-line load limit.
- **Session start**: a hook prints git's facts (branch, default-branch tip, commits since
  the index was written). Memory is a set of claims about that state; verify a path,
  command or flag a memory names before recommending it, and do not ask "what would you
  like to work on" when the session opened with a task.
- **When the default branch moves** (a merge landed), the Stop hook blocks once and asks
  for the `memory-prune` skill: delete or re-date what the commits made stale, move
  anything ledger-shaped out of the index into a dated leaf, and leave the index no
  larger than it was. Auto memory adds during the session; this pass is the only thing
  that removes. Run it too when the user says "save context" or "wrap up".
- **Friction log**: `~/.claude/friction-log.md`, shared by every session on this machine,
  one line per incident: `YYYY-MM-DD | project | symptom as observed | what fixed it`.
  Append only when time was actually lost mid-session to tooling, an environment, a
  harness or a service - never to a bug in the code being worked on - and only once the
  fix is confirmed. **Read it first when a tool fails mysteriously**, before debugging
  from scratch. Keep it objective and under 60 lines: no narrative, the symptom in the
  words it appeared in (that is what the next session greps for), the fix as a command
  or a one-clause rule. On every memory-prune pass, prune it too: delete entries whose
  cause is gone for good (a fix committed, a tool upgraded), merge duplicates, and keep
  the rest.

## Angular

Angular repos only; ignore everywhere else.

Components, pages, and layouts use `templateUrl` and `styleUrl`, never inline `template` or `styles` in `@Component`. Every Angular component, page, and layout gets its own `.ts`, `.html`, and `.scss` file.

## Browser and Playwright

Brave (`/usr/bin/brave`) is the only browser on this machine. Google Chrome and standalone Chromium are not installed: never install or launch them.

That bans those binaries and release channels, not the word: Playwright's `chromium` browser type and the MCP server's `--browser chromium` flag are correct and must not be "fixed" - they drive Brave via `executablePath`.

- MCP: use `mcp__playwright__*` (already pinned to Brave). Never call `mcp__plugin_playwright_playwright__*`; it targets Chrome and fails with "Chromium distribution 'chrome' is not found".
- Playwright library and config: `chromium.launch({ executablePath: '/usr/bin/brave' })`. `"brave"` is not a valid `channel` - always `executablePath`, never `channel`.
- Never download browsers: no `npx playwright install chrome|chromium|msedge`. Playwright's own "run `npx playwright install`" error is not permission to run it - point it at Brave instead. Firefox and WebKit are the only engines Brave cannot cover: ask first. Never run `install-deps` (it shells out to `sudo apt-get`; this machine is Arch).
- Tabs: keep at most 2 open (check with `browser_tabs`). Navigate an existing tab instead of opening a new one, and close every tab you no longer need.
- Screenshots: `mkdir -p .claude/playwright-screenshots` first (the server does not create it), then always pass `filename` explicitly, as the project-relative path `.claude/playwright-screenshots/YYYY-MM-DD-<lowercase-hyphenated-description>.png` (e.g. `2026-02-19-login-form-error.png`). Omitting `filename` dumps the shot into `.playwright-mcp/`.
