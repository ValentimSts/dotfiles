# Dotfiles repo design

Date: 2026-09-16

## Goal

Track every relevant user config from this Arch Linux machine in one
repo, organised as GNU Stow packages, with scripts that bootstrap a
fresh install in one command. Two desktop profiles coexist: GNOME
(current daily driver) and Hyprland (in progress).

## Decisions

- Manager: GNU Stow. One top-level directory per tool, each mirroring
  `$HOME`. Reversible with `stow -D`. No templating.
- Secrets never enter the repo. `.bashrc` sources
  `~/.config/shell/secrets.sh` when present; the repo ships
  `secrets.sh.example`. `gh/hosts.yml`, SSH keys, and `.ssh/config`
  are excluded.
- GNOME state is captured as `dconf dump` output per schema path in
  `gnome/dconf/*.ini`, plus an extension UUID list. Scripts export and
  import it.
- Package lists are plain text, one package per line, split into
  `pacman.txt` (official repos), `aur.txt`, `flatpak.txt`,
  `gnome-extensions.txt`.
- Wallpapers (4.5 MB) and VS Code settings + snippets are tracked.

## Layout

```
install.sh                one-shot bootstrap, idempotent, --dry-run, --profile
Makefile                  thin wrappers over scripts/
scripts/lib.sh            logging, prompts, dry-run, helpers
scripts/install-packages.sh
scripts/stow.sh           stow/unstow/restow package sets, backs up conflicts
scripts/gnome-export.sh   dconf + extension list -> gnome/
scripts/gnome-import.sh   gnome/ -> dconf, installs missing extensions
scripts/secrets-init.sh   creates ~/.config/shell/secrets.sh from example
scripts/enable-services.sh systemd user units per profile
packages/*.txt
gnome/dconf/*.ini, gnome/extensions.txt
<tool>/...                stow packages
```

Stow packages: bash, git, gh, kitty, nvim, neofetch, vscode, xdg,
hypr, waybar, rofi, eww, waypaper, wallpapers, color-schemes,
libinput-gestures, systemd.

Profiles: `common` = bash git gh kitty nvim neofetch vscode xdg
color-schemes wallpapers. `gnome` = common. `hyprland` = common +
hypr waybar rofi eww waypaper libinput-gestures systemd.

## Out of scope

Browser profiles, application caches, `~/.claude`, `~/.codex`,
SSH, GPG, credentials of any kind, `~/.themes` (installed by package
or by hand).
