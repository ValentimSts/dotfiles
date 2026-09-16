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
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Angular CLI completion (only if ng is on PATH)
command -v ng >/dev/null 2>&1 && source <(ng completion script)

# Apply pywal colors
# cat ~/.cache/wal/sequences

#
#  Secrets (never committed; see ~/.config/shell/secrets.sh.example)
# -----------------------------
[ -f "$HOME/.config/shell/secrets.sh" ] && . "$HOME/.config/shell/secrets.sh"
