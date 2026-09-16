#!/usr/bin/env bash
# Link (or unlink) dotfile packages into $HOME with GNU Stow.
#
# Usage: scripts/stow.sh [stow|unstow|restow] [--profile P] [--dry-run] [PKG...]
#   With no PKG arguments, the profile's package set is used.
#   Existing real files that would conflict are moved to $BACKUP_DIR first.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

action="stow"; profile="gnome"; explicit=()
while [ $# -gt 0 ]; do
  case "$1" in
    stow|unstow|restow) action="$1" ;;
    --profile) profile="$2"; shift ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) explicit+=("$1") ;;
  esac
  shift
done

need_cmd stow
cd "$DOTFILES_DIR"

if [ ${#explicit[@]} -gt 0 ]; then
  packages=("${explicit[@]}")
else
  mapfile -t packages < <(packages_for_profile "$profile")
fi

for p in "${packages[@]}"; do
  [ -d "$p" ] || die "no such package directory: $p"
done

# backup_conflicts <pkg>: move any non-symlink file in $HOME that a package
# would overwrite into $BACKUP_DIR, preserving its relative path.
backup_conflicts() {
  local pkg="$1" rel target
  while IFS= read -r -d '' f; do
    rel="${f#"$pkg"/}"
    target="$HOME/$rel"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      log "backing up $target"
      run mkdir -p "$BACKUP_DIR/$(dirname "$rel")"
      run mv "$target" "$BACKUP_DIR/$rel"
    fi
  done < <(find "$pkg" -type f -print0)
}

stow_flags=(--target="$HOME" --verbose=1)
if [ "$DRY_RUN" = "1" ]; then
  stow_flags+=(--simulate)
  warn "dry run: conflicts Stow reports below are exactly the files a real run moves to $BACKUP_DIR"
fi

case "$action" in
  stow)
    for p in "${packages[@]}"; do backup_conflicts "$p"; done
    stow "${stow_flags[@]}" --stow "${packages[@]}"
    ;;
  restow)
    for p in "${packages[@]}"; do backup_conflicts "$p"; done
    stow "${stow_flags[@]}" --restow "${packages[@]}"
    ;;
  unstow)
    stow "${stow_flags[@]}" --delete "${packages[@]}"
    ;;
esac
ok "$action complete: ${packages[*]}"
