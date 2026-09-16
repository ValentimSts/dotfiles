#!/usr/bin/env bash
# Bootstrap this machine from the dotfiles repo.
#
# Usage: ./install.sh [--profile gnome|hyprland] [--skip-packages] [--skip-gnome]
#                     [--skip-services] [--dry-run] [--yes]
#
# Steps, in order: packages -> stow -> secrets -> gnome settings -> services.
# Every step is idempotent, so re-running after a failure is safe.

source "$(dirname "${BASH_SOURCE[0]}")/scripts/lib.sh"

profile="gnome"; skip_pkgs=0; skip_gnome=0; skip_services=0
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) profile="$2"; shift ;;
    --skip-packages) skip_pkgs=1 ;;
    --skip-gnome) skip_gnome=1 ;;
    --skip-services) skip_services=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --yes|-y) ASSUME_YES=1 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
  shift
done
export DRY_RUN ASSUME_YES="${ASSUME_YES:-0}"

[ -f /etc/arch-release ] || warn "this does not look like Arch Linux; package steps may fail"

log "dotfiles: $DOTFILES_DIR"
log "profile:  $profile"
[ "$DRY_RUN" = "1" ] && warn "dry run: nothing will be changed"

confirm "Proceed?" || die "aborted"

S="$DOTFILES_DIR/scripts"
dry=(); [ "$DRY_RUN" = "1" ] && dry=(--dry-run)

if [ "$skip_pkgs" = "0" ]; then
  log "step 1/5: packages"
  "$S/install-packages.sh" "${dry[@]}"
else
  log "step 1/5: packages (skipped)"
fi

log "step 2/5: stow --profile $profile"
"$S/stow.sh" stow --profile "$profile" "${dry[@]}"

log "step 3/5: secrets"
"$S/secrets-init.sh"

if [ "$skip_gnome" = "0" ] && [ "$profile" = "gnome" ]; then
  log "step 4/5: gnome settings"
  "$S/gnome-import.sh" "${dry[@]}"
else
  log "step 4/5: gnome settings (skipped)"
fi

if [ "$skip_services" = "0" ]; then
  log "step 5/5: services"
  "$S/enable-services.sh" --profile "$profile" "${dry[@]}"
else
  log "step 5/5: services (skipped)"
fi

ok "done. Open a new shell (or log out and in) to pick everything up."
[ -d "$BACKUP_DIR" ] && log "replaced files were backed up to $BACKUP_DIR"
exit 0
