# dotfiles

Personal configuration for Arch Linux, managed with [GNU Stow](https://www.gnu.org/software/stow/).
Two desktop profiles share one repo: **GNOME** (daily driver) and **Hyprland** (work in progress).

## Quick start

```sh
git clone https://github.com/ValentimSts/dotfiles ~/projects/Personal/dotfiles
cd ~/projects/Personal/dotfiles
./install.sh                     # GNOME profile: packages, links, secrets, dconf, services
./install.sh --profile hyprland  # same, but links the Hyprland stack instead of loading dconf
./install.sh --dry-run           # print every action without touching anything
```

`install.sh` is idempotent. Re-run it after a failure or after pulling changes.
Any real file it would overwrite is moved to `~/.dotfiles-backup/<timestamp>/` first.

## Layout

Every top-level directory that is not listed below is a Stow package whose
contents mirror `$HOME`. For example `kitty/.config/kitty/kitty.conf` is linked
to `~/.config/kitty/kitty.conf`.

| Path | Purpose |
| --- | --- |
| `install.sh` | One-shot bootstrap. Runs the scripts below in order. |
| `Makefile` | Shortcuts: `make stow`, `make gnome-export`, `make help`, ... |
| `scripts/` | Individual steps. Each accepts `--help` and `--dry-run`. |
| `packages/` | `pacman.txt`, `aur.txt`, `flatpak.txt`: one package per line. |
| `gnome/` | `dconf/*.ini` exports and `extensions.txt` (enabled extension UUIDs). |

### Packages by profile

| Profile | Stow packages |
| --- | --- |
| common | `bash` `git` `gh` `kitty` `nvim` `neofetch` `vscode` `xdg` `color-schemes` `wallpapers` |
| gnome | common |
| hyprland | common + `hypr` `waybar` `rofi` `eww` `waypaper` `libinput-gestures` `systemd` |

## Day-to-day

| Task | Command |
| --- | --- |
| Link a single package | `scripts/stow.sh stow kitty` |
| Unlink everything for a profile | `make unstow PROFILE=hyprland` |
| Added a new file inside a package | `make restow` |
| Changed GNOME settings you want to keep | `make gnome-export`, then commit |
| Installed or removed packages | `make export-packages`, then commit |
| New machine, GNOME only, no package install | `./install.sh --skip-packages` |

Adding a new tool: create `<tool>/` mirroring the path under `$HOME`, add the name
to the right array in `scripts/lib.sh`, and run `make restow`.

## Secrets

Nothing sensitive is tracked. `~/.bashrc` sources `~/.config/shell/secrets.sh`
when it exists; that file is gitignored and `scripts/secrets-init.sh` creates it
from `bash/.config/shell/secrets.sh.example`. SSH keys, `gh` OAuth tokens and
browser profiles are deliberately excluded.

## GNOME settings

`scripts/gnome-export.sh` dumps a fixed list of dconf paths (shell, extensions,
interface, window manager, peripherals, keybindings, power, Nautilus) into
`gnome/dconf/`. `scripts/gnome-import.sh` loads them back and enables every
extension in `gnome/extensions.txt`, installing missing ones through
`gnome-extensions-cli` when it is available. Log out and in after importing.

## License

GPL-3.0. See `LICENSE`.
