#!/usr/bin/python3
"""PreToolUse hook: back the Destructive Actions rules in ~/.claude/CLAUDE.md.

Reads the tool call on stdin and blocks two kinds of command, telling Claude
why. Everything else runs as usual, and the hook prints nothing.

  never      a plain force push, or any force push to the default branch.
  user only  history rewrites, discarding uncommitted work, a forced branch
             delete, a recursive rm outside the project, dropping database
             tables. Claude is told to hand the command to the user to run.

Both are a block, not a permission prompt: Orca answers permission prompts by
itself when its chats have full access, so a prompt would stop nothing there.

A backstop, not a sandbox. It reads the command the way a shell would, through
quotes, substitutions and `bash -c`, but it cannot follow a script file, an
alias or a path built at run time, and those run unchecked. If the hook itself
fails it lets the command through, so a bug here cannot stop every session on
the machine.

Registered in ~/.claude/settings.json for Bash and for the SQL tools of MCP
servers. scripts/test_guard_destructive.py in the dotfiles repo covers it.
"""

import json
import os
import re
import subprocess
import sys

SHELLS = {"bash", "sh", "zsh", "dash"}
# Words a shell allows before the command itself.
KEYWORDS = {"{", "}", "!", "if", "then", "else", "elif", "do", "while", "until", "time"}
# Commands that run the command given as their arguments.
WRAPPERS = {"sudo", "doas", "env", "command", "builtin", "exec", "nohup", "nice", "ionice", "setsid", "stdbuf", "timeout", "xargs"}
SQL_CLIENTS = {"psql", "pgcli", "mysql", "mariadb", "sqlite3", "duckdb", "supabase", "wrangler", "turso"}
PACKAGE_RUNNERS = {"npx", "pnpm", "bunx", "bun", "yarn", "npm"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
REBASE_IN_PROGRESS = {"--continue", "--abort", "--skip", "--quit", "--edit-todo", "--show-current-patch"}
EVERYTHING = {".", "./", ":/", "*"}
# Cheap test for a command that cannot be any of the above.
MAYBE = re.compile(r"\b(git|rm|supabase|prisma)\b|drop|truncate", re.IGNORECASE)
SQL_DESTRUCTIVE = re.compile(r"\b(drop\s+(table|column|database|schema)|truncate\s+(table\s+)?[\w\"`.]+)", re.IGNORECASE)
MIGRATION_RESET = re.compile(r"\b(supabase\s+db\s+reset|prisma\s+migrate\s+reset)\b")
ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
REDIRECTION = re.compile(r"^\d*(>>?|<)")
HEREDOC = re.compile(r"(?<!<)<<-?\s*(['\"]?)([A-Za-z_]\w*)\1")
HEREDOC_TO_SHELL = re.compile(r"(^|[;&|(]\s*)(\w+=\S*\s+)*(%s)\b[^;&|]*$" % "|".join(sorted(SHELLS)))
# Stands in a word for a substitution, whose value is only known at run time.
UNKNOWN = "\x00"
# Scratch space, where a recursive rm is routine.
TEMP_ROOTS = ["/tmp", "/var/tmp", os.path.expanduser("~/.cache")]
TEMP_ROOTS += [os.environ[name] for name in ("TMPDIR", "XDG_RUNTIME_DIR") if os.environ.get(name)]


def drop_heredoc_bodies(text):
    """Remove the body of each here-document, unless a shell is going to run it."""
    kept = []
    end = None  # the line that closes the here-document being skipped
    for line in text.split("\n"):
        if end is not None:
            if line.strip() == end:
                end = None
            continue
        kept.append(line)
        match = HEREDOC.search(line)
        if match and not HEREDOC_TO_SHELL.search(line[: match.start()]):
            end = match.group(2)
    return "\n".join(kept)


def split_commands(text):
    """Split shell text into its simple commands, each a list of words.

    Commands inside $(...), backticks and (...) come out as commands of their
    own, and the word a substitution sat in is marked UNKNOWN.
    """
    commands = []
    frames = [[[], None]]  # one per substitution depth: [words so far, word in progress]
    stack = ["command"]  # what the scanner is inside: command, dq, sub, backtick, paren

    def add(chars):
        frame = frames[-1]
        frame[1] = (frame[1] or "") + chars

    def end_word():
        frame = frames[-1]
        if frame[1] is not None:
            frame[0].append(frame[1])
            frame[1] = None

    def end_command():
        end_word()
        frame = frames[-1]
        if frame[0]:
            commands.append(frame[0])
            frame[0] = []

    def enter(kind):
        add(UNKNOWN)
        frames.append([[], None])
        stack.append(kind)

    def leave():
        end_command()
        if len(frames) > 1:
            frames.pop()
        stack.pop()

    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        inside = stack[-1]
        substitution = text.startswith("$(", i) and not text.startswith("$((", i)
        if inside == "dq":
            if ch == "\\" and i + 1 < n:
                add(text[i + 1])
                i += 2
            elif ch == '"':
                stack.pop()
                i += 1
            elif substitution:
                enter("sub")
                i += 2
            elif ch == "`":
                enter("backtick")
                i += 1
            else:
                add(ch)
                i += 1
        elif ch == "\\" and i + 1 < n:
            if text[i + 1] != "\n":  # a backslash at the end of a line joins the lines
                add(text[i + 1])
            i += 2
        elif ch == "'":
            close = text.find("'", i + 1)
            close = n if close < 0 else close
            add(text[i + 1 : close])
            i = close + 1
        elif ch == '"':
            add("")
            stack.append("dq")
            i += 1
        elif ch == "`":
            if inside == "backtick":
                leave()
            else:
                enter("backtick")
            i += 1
        elif substitution:
            enter("sub")
            i += 2
        elif ch == "#" and frames[-1][1] is None:
            newline = text.find("\n", i)
            i = n if newline < 0 else newline
        elif ch in " \t":
            end_word()
            i += 1
        elif ch in "\n;&|":
            end_command()
            i += 1
        elif ch == "(":
            end_command()
            stack.append("paren")
            i += 1
        elif ch == ")":
            if inside == "sub":
                leave()
            else:
                end_command()
                if inside == "paren":
                    stack.pop()
            i += 1
        else:
            add(ch)
            i += 1
    while len(frames) > 1:
        leave()
    end_command()
    return commands


def without_redirections(words):
    kept = []
    skip = False
    for word in words:
        if skip:
            skip = False
        elif REDIRECTION.match(word):
            skip = REDIRECTION.fullmatch(word) is not None  # "> file": the target is the next word
        else:
            kept.append(word)
    return kept


def has_short(args, letter):
    """Whether a short option is given, alone or in a cluster: -f, -fd, -xdf."""
    for arg in args:
        if arg == "--":
            return False
        if re.fullmatch(r"-[A-Za-z]+", arg) and letter in arg:
            return True
    return False


def has_long(args, *names):
    for arg in args:
        if arg == "--":
            return False
        if arg.split("=", 1)[0] in names:
            return True
    return False


def positionals(args):
    found = []
    for index, arg in enumerate(args):
        if arg == "--":
            return found + args[index + 1 :]
        if not arg.startswith("-"):
            found.append(arg)
    return found


def git_output(directory, *args):
    try:
        result = subprocess.run(["git", "-C", directory, *args], capture_output=True, text=True, timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


class Guard:
    def __init__(self, cwd):
        self.start = cwd
        self.cwd = cwd  # follows "cd"; None once it can no longer be followed
        self.variables = {}
        self.never = []
        self.user_only = []

    # -- reading the command ---------------------------------------------

    def check_shell(self, text):
        for words in split_commands(drop_heredoc_bodies(text)):
            self.check_command(without_redirections(words))

    def expand(self, word):
        """A word with ~ and its variables filled in, or None if one is unknown."""
        def value(match):
            name = match.group(1) or match.group(2)
            found = self.variables.get(name, os.environ.get(name))
            return UNKNOWN if found is None else found

        word = re.sub(r"\$\{(\w+)\}|\$(\w+)", value, word)
        if UNKNOWN in word or "$" in word:
            return None
        return os.path.expanduser(word)

    def resolve(self, path):
        if os.path.isabs(path):
            return os.path.normpath(path)
        return None if self.cwd is None else os.path.normpath(os.path.join(self.cwd, path))

    def check_command(self, words):
        while words and words[0] in KEYWORDS:
            words = words[1:]
        assignments = []
        while words and ASSIGNMENT.match(words[0]):
            assignments.append(words[0])
            words = words[1:]
        if not words:
            for assignment in assignments:
                name, _, raw = assignment.partition("=")
                self.variables[name] = self.expand(raw)
            return

        name = os.path.basename(words[0])
        args = words[1:]
        if name in WRAPPERS:
            # Whatever follows the wrapper's own options is the command.
            while args and (args[0].startswith("-") or ASSIGNMENT.match(args[0]) or re.fullmatch(r"[\d.]+[smhd]?", args[0])):
                args = args[1:]
            self.check_command(args)
        elif name in SHELLS:
            for index, arg in enumerate(args[:-1]):
                if re.fullmatch(r"-[a-z]*c", arg):
                    self.check_shell(args[index + 1])
                    break
        elif name == "eval":
            self.check_shell(" ".join(args))
        elif name == "cd":
            target = self.expand(args[0]) if len(args) == 1 else None
            self.cwd = self.resolve(target) if target else None
        elif name == "git":
            self.check_git(args)
        elif name == "rm":
            self.check_rm(args)
        if name in SQL_CLIENTS | PACKAGE_RUNNERS:
            self.check_database(" ".join(words))

    # -- the rules ---------------------------------------------------------

    def check_git(self, args):
        directory = self.cwd or self.start
        while args and args[0].startswith("-"):
            if args[0] == "-C" and len(args) > 1:
                directory = os.path.normpath(os.path.join(directory, self.expand(args[1]) or "."))
            args = args[2:] if args[0] in GIT_OPTIONS_WITH_VALUE else args[1:]
        if not args:
            return
        command, args = args[0], args[1:]

        if command == "push":
            self.check_push(args, directory)
        elif command == "rebase":
            if not has_long(args, *REBASE_IN_PROGRESS):
                self.user_only.append("`git rebase` rewrites history")
        elif command == "pull":
            if has_short(args, "r") or (has_long(args, "--rebase") and "--rebase=false" not in args):
                self.user_only.append("`git pull --rebase` rewrites local history")
        elif command == "commit":
            if has_long(args, "--amend"):
                self.user_only.append("`git commit --amend` rewrites the last commit")
        elif command == "reset":
            if has_long(args, "--hard"):
                self.user_only.append("`git reset --hard` discards uncommitted work")
        elif command == "clean":
            forced = has_short(args, "f") or has_long(args, "--force")
            dry_run = has_short(args, "n") or has_long(args, "--dry-run")
            if forced and not dry_run:
                self.user_only.append("`git clean -f` deletes untracked files")
        elif command == "checkout":
            if has_short(args, "f") or has_long(args, "--force"):
                self.user_only.append("`git checkout --force` discards uncommitted work")
            elif EVERYTHING & set(positionals(args)):
                self.user_only.append("`git checkout .` discards uncommitted work")
        elif command == "restore":
            staged = has_long(args, "--staged") or has_short(args, "S")
            worktree = has_long(args, "--worktree") or has_short(args, "W")
            if (worktree or not staged) and EVERYTHING & set(positionals(args)):
                self.user_only.append("`git restore .` discards uncommitted work")
        elif command == "stash":
            if args[:1] in (["drop"], ["clear"]):
                self.user_only.append("`git stash %s` deletes stashed work" % args[0])
        elif command == "branch":
            delete = has_short(args, "d") or has_long(args, "--delete")
            if has_short(args, "D") or (delete and (has_short(args, "f") or has_long(args, "--force"))):
                self.user_only.append("`git branch -D` deletes a branch that may not be merged")
        elif command in ("filter-branch", "filter-repo"):
            self.user_only.append("`git %s` rewrites history" % command)

    def check_push(self, args, directory):
        targets = positionals(args)[1:]  # the first positional is the remote
        plain = has_short(args, "f") or has_long(args, "--force") or any(t.startswith("+") for t in targets)
        lease = has_long(args, "--force-with-lease")
        if plain:
            self.never.append(
                "a plain force push is never allowed. If the user asked for a force push, "
                "use --force-with-lease, and never on the default branch"
            )
        elif lease and self.pushes_to_default(args, targets, directory):
            self.never.append("a force push to the default branch is never allowed")
        elif lease:
            self.user_only.append("`git push --force-with-lease` overwrites the remote branch")

    def pushes_to_default(self, args, targets, directory):
        if has_long(args, "--all", "--mirror"):
            return True
        default = git_output(directory, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
        defaults = {default.split("/", 1)[-1]} if default else {"main", "master"}
        current = git_output(directory, "rev-parse", "--abbrev-ref", "HEAD")
        branches = [t.rsplit(":", 1)[-1].replace("refs/heads/", "") for t in targets] or ["HEAD"]
        return any((current if branch == "HEAD" else branch) in defaults for branch in branches)

    def check_rm(self, args):
        if not (has_short(args, "r") or has_short(args, "R") or has_long(args, "--recursive")):
            return
        project = os.path.normpath(git_output(self.start, "rev-parse", "--show-toplevel") or self.start)
        for target in positionals(args):
            expanded = self.expand(target)
            if expanded is None:
                continue  # built at run time; Claude Code's own rm check still covers / and ~
            wildcard = re.search(r"[*?\[]", expanded)
            if wildcard:
                expanded = os.path.dirname(expanded[: wildcard.start()]) or "."
            path = self.resolve(expanded)
            if path is None:
                continue
            # The project itself, or a directory holding it, is never "inside" anything.
            holds_project = (project + os.sep).startswith(path.rstrip(os.sep) + os.sep)
            inside = any(path.startswith(os.path.normpath(root) + os.sep) for root in [project] + TEMP_ROOTS)
            if holds_project or not inside:
                self.user_only.append("`rm -r %s` deletes outside this project" % target)

    def check_database(self, text):
        if MIGRATION_RESET.search(text):
            self.user_only.append("this resets the database")
        elif SQL_DESTRUCTIVE.search(text):
            self.user_only.append("this drops or truncates database tables")


def decide(tool_name, tool_input, cwd):
    """(verdict, reason) for a tool call, where verdict is never, user-only or None."""
    guard = Guard(cwd)
    if tool_name == "Bash":
        command = tool_input.get("command") or ""
        if MAYBE.search(command):
            guard.check_shell(command)
    elif tool_name.startswith("mcp__"):
        guard.check_database(json.dumps(tool_input))
    if guard.never:
        return "never", "Blocked by guard-destructive.py: " + "; ".join(guard.never) + "."
    if guard.user_only:
        reasons = "; ".join(dict.fromkeys(guard.user_only))
        return "user-only", (
            "Blocked by guard-destructive.py: " + reasons + ". Only the user runs this. Do not "
            "reword it or reach the same result another way. If the user asked for exactly this, "
            "give them the command to run themselves; otherwise stop and ask what they want."
        )
    return None, ""


def main():
    try:
        call = json.load(sys.stdin)
        verdict, reason = decide(call.get("tool_name") or "", call.get("tool_input") or {}, call.get("cwd") or os.getcwd())
    except Exception as error:  # fail open: see the module docstring
        print("guard-destructive.py failed and let the command through: %r" % error, file=sys.stderr)
        return 0
    if verdict:
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            sys.stdout,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
