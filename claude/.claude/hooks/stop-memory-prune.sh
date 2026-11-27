#!/bin/sh
# Stop hook: once per session, after the default branch has moved (a merge landed, so
# memory's facts about tips, branches, PRs and follow-ups are now stale), block the stop
# once with an instruction to run the memory-prune skill. Every other turn it exits 0 in
# a few milliseconds.
#
# Guards, in order: a hook already blocking (stop_hook_active), no git repo, no memory
# directory for this project, the default branch has not moved since session start, this
# tip was already handled, or a memory file was edited after the branch last moved (the
# pass already ran this turn). It fires at most once every four hours per session, never
# in a loop, and lists everything that landed since it last fired.

input=$(cat)
[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')
[ -n "$cwd" ] && [ -n "$sid" ] && cd "$cwd" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

root=$(git rev-parse --show-toplevel)
memdir="$HOME/.claude/projects/$(printf '%s' "$root" | tr '/' '-')/memory"
[ -f "$memdir/MEMORY.md" ] || exit 0

default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
[ -n "$default" ] || default=main
state="$HOME/.claude/state"
start_file="$state/$sid.$default-at-start"
now=$(git rev-parse --short "$default" 2>/dev/null)
[ -n "$now" ] || exit 0

# A session that began before this hook existed has no record: take the current tip as
# the baseline and let this turn end.
if [ ! -f "$start_file" ]; then
    mkdir -p "$state"; printf '%s\n' "$now" > "$start_file"; exit 0
fi
start=$(cat "$start_file")
[ "$start" = "$now" ] && exit 0

marker="$state/$sid.pruned-$now"
[ -f "$marker" ] && exit 0
touch "$marker"

# At most one pass every four hours per session: a session that lands a dozen changes would
# otherwise spend a turn on each. The next pass lists everything landed since the last one.
last="$state/$sid.pruned-last"
[ -n "$(find "$last" -mmin -240 2>/dev/null)" ] && exit 0
touch "$last"

# Report from the last tip this hook handled in this session, not from its start, so a
# second firing lists only the new commits.
handled_file="$state/$sid.$default-handled"
since=$start
[ -f "$handled_file" ] && since=$(cat "$handled_file")
printf '%s\n' "$now" > "$handled_file"
[ "$since" = "$now" ] && exit 0

# A memory file edited after the branch last moved means the pass already ran this turn.
# Git touches the branch's reflog file on every update of the branch.
reflog=$(git rev-parse --path-format=absolute --git-path "logs/refs/heads/$default" 2>/dev/null)
if [ -f "$reflog" ] && [ -n "$(find "$memdir" -name '*.md' -newer "$reflog" 2>/dev/null | head -n 1)" ]; then
    exit 0
fi

{
    echo "memory-prune due: $default moved from $since to $now during this session."
    git log --oneline "$since..$now" 2>/dev/null | head -8 | sed 's/^/  /'
    echo "Before stopping, run the memory-prune skill over $memdir: re-date or delete every memory these commits made stale (tips, branches, PR numbers, open follow-ups), move anything ledger-shaped out of MEMORY.md into a dated leaf file, and leave the index no larger than you found it. Then stop."
} >&2
exit 2
