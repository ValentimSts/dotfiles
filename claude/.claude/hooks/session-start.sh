#!/bin/sh
# SessionStart hook: print the facts a session should verify memory against, so the
# always-loaded MEMORY.md is read as claims about a state git can contradict. Plain
# stdout from this event is added to the model's context. Also records the default
# branch's tip for this session, which the Stop hook compares against to decide when a
# memory prune is due.
#
# Cheap by design: a handful of git commands, no model call, under 15 lines of output.

input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

root=$(git rev-parse --show-toplevel)
default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
[ -n "$default" ] || default=main
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
tip=$(git rev-parse --short "$default" 2>/dev/null)

state="$HOME/.claude/state"
mkdir -p "$state"
find "$state" -type f -mtime +7 -delete 2>/dev/null   # one file per session; keep a week
[ -n "$sid" ] && [ -n "$tip" ] && printf '%s\n' "$tip" > "$state/$sid.$default-at-start"

echo "Session context from git (verify memory against this, not the other way round):"
echo "  repo: $root"
echo "  branch: $branch  ${default} tip: ${tip:-?}  dirty files: $(git status --short | wc -l)"
git log --oneline -3 "$default" 2>/dev/null | sed 's/^/  /'

memdir="$HOME/.claude/projects/$(printf '%s' "$root" | tr '/' '-')/memory"
if [ -f "$memdir/MEMORY.md" ]; then
    written=$(date -r "$memdir/MEMORY.md" +%Y-%m-%dT%H:%M:%S)
    since=$(git rev-list --count --since="$written" "$default" 2>/dev/null)
    echo "  MEMORY.md written ${written%T*}; $since commit(s) on $default since. Facts about tips, PRs and branches older than that are claims."
fi
exit 0
