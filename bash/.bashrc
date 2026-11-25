# shellcheck shell=bash
#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
PS1='[\u@\h \W]\$ '

# Prompt: starship when available (see ~/.config/starship.toml), plain PS1 otherwise.
# Blank line between prompts, but not before the first one (avoids a gap at the top).
starship_blank_line() {
  if [ -n "${STARSHIP_FIRST_PROMPT_DONE-}" ]; then
    printf '\n'
  else
    STARSHIP_FIRST_PROMPT_DONE=1
  fi
}
# After the screen is cleared the next prompt counts as a first prompt again.
clear() { command clear "$@"; STARSHIP_FIRST_PROMPT_DONE=; }
reset() { command reset "$@"; STARSHIP_FIRST_PROMPT_DONE=; }
if command -v starship >/dev/null 2>&1; then
  # shellcheck disable=SC2034  # read by starship's init script
  starship_precmd_user_func="starship_blank_line"
  eval "$(starship init bash)"
fi

#
#  Environment Variables
# -----------------------------
export CONFIG_DIR="$HOME/.config"
export ANDROID_HOME="$HOME/Android/Sdk"
export JAVA_HOME="/usr/lib/jvm/default/"

#
#  $PATH
# -----------------------------
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
export PATH="$PATH:$HOME/.local/bin"
export PATH="$PATH:$HOME/.foundry/bin"

# pnpm
export PNPM_HOME="$HOME/.local/share/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac

#
#  Tooling
# -----------------------------
export NVM_DIR="$HOME/.nvm"
# Sourcing nvm.sh costs about 200 ms a shell. Put the default Node on PATH
# straight from its folder instead, and load nvm itself the first time it is
# called. An alias this cannot resolve (lts/*, node) falls back to loading now.
load_nvm() {
  unset -f nvm load_nvm
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
}
if [ -s "$NVM_DIR/nvm.sh" ]; then
  nvm_default=""
  [ -r "$NVM_DIR/alias/default" ] && read -r nvm_default < "$NVM_DIR/alias/default"
  nvm_bin="$(compgen -G "$NVM_DIR/versions/node/v${nvm_default#v}*/bin" | sort -V | tail -n 1)"
  if [ -n "$nvm_default" ] && [ -n "$nvm_bin" ]; then
    export PATH="$nvm_bin:$PATH"
    nvm() { load_nvm; nvm "$@"; }
  else
    load_nvm
  fi
  unset nvm_default nvm_bin
fi

# Angular CLI completion. `ng completion script` starts Node, so its output is
# kept in a file and only regenerated when ng itself is newer.
if command -v ng >/dev/null 2>&1; then
  ng_completion="${XDG_CACHE_HOME:-$HOME/.cache}/ng-completion.bash"
  if [ ! -s "$ng_completion" ] || [ "$(command -v ng)" -nt "$ng_completion" ]; then
    mkdir -p "$(dirname "$ng_completion")"
    ng completion script > "$ng_completion" 2>/dev/null
  fi
  # shellcheck disable=SC1090  # generated file
  [ -s "$ng_completion" ] && . "$ng_completion"
  unset ng_completion
fi

# Apply pywal colors
# cat ~/.cache/wal/sequences

#
#  Secrets (never committed; see ~/.config/shell/secrets.sh.example)
# -----------------------------
[ -f "$HOME/.config/shell/secrets.sh" ] && . "$HOME/.config/shell/secrets.sh"
