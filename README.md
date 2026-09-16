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
| common | `bash` `starship` `git` `gh` `kitty` `nvim` `neofetch` `vscode` `xdg` `color-schemes` `wallpapers` |
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

## Prompt

The bash prompt is [Starship](https://starship.rs), configured in
`starship/.config/starship.toml`. It shows the full path from `~`, the git branch
with a counted status (`*N` modified, `+N` staged, `?N` untracked, `!N`
conflicts, `>N` ahead, `<N` behind), lines added and removed as `(+N -N)`, the docker context when one is set, and the duration of any
command slower than two seconds. `.bashrc` falls back to the plain Arch
prompt when `starship` is not installed.

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

## Shortcuts

Custom bindings only. Anything not listed keeps the program's default.

### Kitty

Split, tab and hint bindings live in `kitty/.config/kitty/configs/keymaps.conf`.

| Keys | Action |
| --- | --- |
| `ctrl+shift+enter` | Vertical split in the current directory |
| `ctrl+shift+minus` | Horizontal split in the current directory |
| `ctrl+shift+h` `j` `k` `l` | Focus pane left / down / up / right |
| `ctrl+shift+z` | Toggle stack layout (maximise the focused pane) |
| `ctrl+shift+r` | Resize mode: arrows to resize, `esc` to finish |
| `ctrl+shift+w` | Close pane |
| `ctrl+shift+t` | New tab in the current directory |
| `ctrl+shift+q` | Close tab |
| `ctrl+shift+alt+t` | Rename tab |
| `ctrl+shift+left` / `right` | Previous / next tab |
| `ctrl+shift+,` / `.` | Move tab left / right |
| `ctrl+1` ... `ctrl+9` | Jump to tab N |
| `ctrl+shift+e` | Open a URL on screen by hint |
| `ctrl+shift+p` then `f` | Insert a path from the screen by hint |
| `ctrl+shift+p` then `l` | Insert a whole line by hint |
| `ctrl+shift+p` then `w` | Insert a word by hint |
| `ctrl+shift+f` | Open scrollback in Neovim |
| `ctrl+shift+g` | Open the last command's output in Neovim |
| `ctrl+shift+a` then `m` / `l` / `d` | Background opacity more / less / default |
| `ctrl+shift+f5` | Reload the config |
| `shift+enter` | Send a newline without executing (multi-line prompts) |
| `ctrl+shift+b` | Send `ctrl+B` as a CSI-u sequence (for apps that need it) |

The theme follows the desktop colour scheme: `dark-theme.auto.conf` (Catppuccin) and
`light-theme.auto.conf` (e-ink light) are picked automatically.
Remote control is enabled on the `unix:@kitty` socket, so `kitten @` commands
and Neovim plugins such as smart-splits can drive windows from outside.

### Hyprland

`SUPER` is the main modifier. Defined in `hypr/.config/hypr/hyprland.conf`.

| Keys | Action |
| --- | --- |
| `super+enter` | Terminal (kitty) |
| `super+space` | App launcher (rofi) |
| `super+e` | File manager (nautilus) |
| `super+f` | Browser (brave) |
| `super+w` | Wallpaper picker (waypaper) |
| `super+c` | Close window |
| `super+v` | Toggle floating |
| `super+p` | Pseudotile (dwindle) |
| `super+j` | Toggle split direction (dwindle) |
| `super+arrows` | Move focus |
| `super+1` ... `super+0` | Go to workspace 1 to 10 |
| `super+shift+1` ... `0` | Move window to workspace 1 to 10 |
| `super+s` / `super+shift+s` | Toggle / move to the special "magic" workspace |
| `super+scroll` | Next / previous workspace |
| `super+left drag` / `right drag` | Move / resize window |
| `super+shift+l` | Lock screen (hyprlock) |
| `super+shift+r` | Restart waybar |
| `super+m` | Exit Hyprland |
| `print` / `shift+print` | Screenshot window / region (hyprshot) |
| `ctrl+space` | Switch keyboard layout (us / pt) |
| Volume, brightness and media keys | Handled by wpctl, brightnessctl and playerctl |

Touchpad (libinput-gestures): three-finger swipe up or down toggles maximise,
four-finger swipe up toggles fullscreen.

### Neovim

Leader is `space`, local leader is `\`. Defined in `nvim/.config/nvim/lua/keymaps.lua`
and the plugin files under `lua/plugins/`.

| Keys | Action |
| --- | --- |
| `space y` / `space Y` | Yank motion / line to the system clipboard |
| `space d` / `space D` | Delete motion / line to the system clipboard |
| `space p` / `space P` | Paste from the system clipboard after / before the cursor |
| `space ff` | Telescope: find files |
| `space fg` | Telescope: live grep |
| `space fb` | Telescope: buffers |
| `space fh` | Telescope: help tags |
| `space tt` | Toggle light / dark colorscheme |
| `space ?` | which-key: show buffer-local keymaps |
| `ctrl+b` / `ctrl+shift+b` | Open / close the Neo-tree file explorer |
| `K` | LSP hover documentation |

## License

GPL-3.0. See `LICENSE`.
