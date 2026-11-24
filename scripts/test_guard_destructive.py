"""Tests for the Claude Code hook claude/.claude/hooks/guard-destructive.py."""

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

HOOK = pathlib.Path(__file__).resolve().parent.parent / "claude/.claude/hooks/guard-destructive.py"
# No __pycache__ beside the hook: Stow would link it into ~/.claude/hooks.
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("guard_destructive", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    """A repository on a feature branch whose default branch is main."""
    path = tmp_path_factory.mktemp("home") / "project"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "init")
    git(path, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(path, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git(path, "checkout", "-q", "-b", "feat/x")
    (path / "sub").mkdir()
    return path


def bash(command, cwd):
    return guard.decide("Bash", {"command": command}, str(cwd))[0]


ALLOWED = [
    "git status",
    "git push",
    "git push -u origin feat/x",
    "git push origin main",
    "git branch -d feat/done",
    "git rebase --continue",
    "git rebase --abort",
    "git pull",
    "git pull --rebase=false",
    "git reset --soft HEAD~1",
    "git reset HEAD file.txt",
    "git clean -n",
    "git clean -fdn",
    "git checkout main",
    "git checkout -b feat/y",
    "git checkout -- src/one.py",
    "git restore --staged .",
    "git restore src/one.py",
    "git stash",
    "git stash pop",
    "git stash list",
    "git log --oneline --force",
    'git commit -m "docs: explain why git reset --hard and push --force are banned"',
    "echo 'git push --force'",
    "grep -rn 'reset --hard' docs",
    "# git reset --hard\ngit status",
    "rm notes.txt",
    "rm -rf node_modules dist",
    "rm -rf ./build/*",
    "cd sub && rm -rf out",
    "rm -rf /tmp/scratch-123",
    "S=/tmp/work; rm -rf \"$S/out\"",
    "rm -rf \"$(mktemp -d)\"",
    "rm -f /etc/hosts",
    "psql -c 'select count(*) from users'",
    "supabase db push",
    "cat > notes.md <<'EOF'\ngit reset --hard\ngit push --force\nEOF",
    "python3 - <<'EOF'\nprint('git push --force')\nEOF",
]

USER_ONLY = [
    "git rebase main",
    "git rebase -i HEAD~3",
    "git pull --rebase",
    "git pull -r origin main",
    "git commit --amend --no-edit",
    "git reset --hard",
    "git reset --hard HEAD~1",
    "git -C sub reset --hard",
    "git -c core.editor=true rebase -i main",
    "git clean -fd",
    "git clean -xdf",
    "git clean --force",
    "git checkout .",
    "git checkout -- .",
    "git checkout HEAD -- .",
    "git checkout -f main",
    "git restore .",
    "git restore --staged --worktree .",
    "git stash drop",
    "git stash clear",
    "git branch -D feat/old",
    "git branch --delete --force feat/old",
    "git filter-branch --tree-filter true HEAD",
    "git push --force-with-lease",
    "git push --force-with-lease origin feat/x",
    "git push --force-with-lease=feat/x origin feat/x",
    "git status && git reset --hard",
    "git status; git reset --hard",
    "git status\ngit reset --hard",
    "git status || (git reset --hard)",
    "true | git clean -fd",
    "echo $(git reset --hard)",
    'echo "now: $(git reset --hard)"',
    "echo `git reset --hard`",
    "bash -c 'git reset --hard'",
    'bash -lc "git stash drop"',
    "eval 'git reset --hard'",
    "sudo git reset --hard",
    "env GIT_PAGER=cat git reset --hard",
    "timeout 30 git clean -fd",
    "GIT_EDITOR=true git rebase -i main",
    "if true; then git reset --hard; fi",
    "{ git reset --hard; }",
    "git reset \\\n  --hard",
    "/usr/bin/git reset --hard",
    "bash <<'EOF'\ngit reset --hard\nEOF",
    "git reset --hard > /dev/null 2>&1",
    "rm -rf /etc/nginx",
    "rm -rf ~/Documents",
    "rm -rf ~/.cache/../Documents",
    "rm -rf ..",
    "rm -rf .",
    "rm --recursive /opt/thing",
    "cd /opt && rm -rf thing",
    "D=/opt/thing; rm -rf $D",
    "rm -rf /opt/things/*",
    "rm -rf build > /dev/null; rm -rf /opt/thing",
    "supabase db reset",
    "npx supabase db reset --linked",
    "pnpm exec prisma migrate reset",
    "psql -c 'DROP TABLE users'",
    'psql "$DATABASE_URL" -c "truncate table sessions"',
    "sqlite3 app.db 'alter table users drop column age'",
]

NEVER = [
    "git push --force",
    "git push -f",
    "git push -fu origin feat/x",
    "git push origin feat/x --force",
    "git push origin +feat/x",
    "git -C sub push --force origin feat/x",
    "git push --force-with-lease origin main",
    "git push --force-with-lease origin HEAD:main",
    "git push --force-with-lease origin feat/x:refs/heads/main",
    "git push --force-with-lease --all",
    "git status && git push --force",
    "bash -c 'git push -f'",
    "git reset --hard && git push --force",
]


@pytest.mark.parametrize("command", ALLOWED)
def test_allowed(command, repo):
    assert bash(command, repo) is None


@pytest.mark.parametrize("command", USER_ONLY)
def test_left_to_the_user(command, repo):
    assert bash(command, repo) == "user-only"


@pytest.mark.parametrize("command", NEVER)
def test_never_allowed(command, repo):
    assert bash(command, repo) == "never"


def test_lease_push_of_the_default_branch_itself_is_never_allowed(repo):
    git(repo, "checkout", "-q", "main")
    try:
        assert bash("git push --force-with-lease", repo) == "never"
        assert bash("git push --force-with-lease origin HEAD", repo) == "never"
    finally:
        git(repo, "checkout", "-q", "feat/x")


def test_rm_inside_a_subdirectory_of_the_project_is_allowed(repo):
    assert bash("rm -rf ../sub/out", repo / "sub") is None


def test_rm_beside_the_project_is_left_to_the_user_unless_it_is_scratch_space(repo, monkeypatch):
    # The test repository lives under /tmp, which is scratch space by default.
    assert bash("rm -r ../sibling", repo) is None
    monkeypatch.setattr(guard, "TEMP_ROOTS", [])
    assert bash("rm -r ../sibling", repo) == "user-only"


def test_sql_tools_of_mcp_servers(repo):
    decide = guard.decide
    assert decide("mcp__supabase__execute_sql", {"query": "drop table users"}, str(repo))[0] == "user-only"
    assert decide("mcp__supabase__execute_sql", {"query": "select 1"}, str(repo))[0] is None


def test_other_tools_are_ignored(repo):
    assert guard.decide("Write", {"file_path": "x", "content": "git push --force"}, str(repo))[0] is None


def run_hook(payload):
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)


@pytest.mark.parametrize("command, reason", [("git push -f", "force push"), ("git reset --hard", "Only the user runs this")])
def test_both_verdicts_block_in_the_hook_decision_format(command, reason, repo):
    result = run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(repo)}))
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert result.returncode == 0
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert reason in output["permissionDecisionReason"]


def test_an_allowed_command_prints_nothing(repo):
    result = run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(repo)}))
    assert (result.returncode, result.stdout) == (0, "")


def test_bad_input_fails_open():
    result = run_hook("not json")
    assert (result.returncode, result.stdout) == (0, "")
    assert "let the command through" in result.stderr
