# Thin wrappers over scripts/. Run `make help` for the list.
PROFILE ?= gnome
SHELL := /usr/bin/env bash

.PHONY: help install stow unstow restow packages packages-diff gnome-export gnome-import secrets services color-schemes color-schemes-check lint test check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install: ## Full bootstrap for PROFILE (default: gnome)
	./install.sh --profile $(PROFILE)

stow: ## Link packages for PROFILE into HOME
	scripts/stow.sh stow --profile $(PROFILE)

restow: ## Re-link packages for PROFILE (after adding files)
	scripts/stow.sh restow --profile $(PROFILE)

unstow: ## Remove links for PROFILE
	scripts/stow.sh unstow --profile $(PROFILE)

packages: ## Install pacman, AUR and flatpak packages for PROFILE
	scripts/install-packages.sh --profile $(PROFILE)

packages-diff: ## Show where packages/*.txt and this machine differ
	scripts/packages-diff.sh

gnome-export: ## Dump dconf settings and extension list into gnome/
	scripts/gnome-export.sh

gnome-import: ## Load gnome/ into dconf and enable extensions
	scripts/gnome-import.sh

secrets: ## Create ~/.config/shell/secrets.sh from the example
	scripts/secrets-init.sh

services: ## Enable systemd services for PROFILE
	scripts/enable-services.sh --profile $(PROFILE)

color-schemes: ## Render every colour scheme port from color-schemes/.../schemes/*.yaml
	scripts/build-color-schemes.py

color-schemes-check: ## Fail if a committed port is stale (run before committing a palette change)
	scripts/build-color-schemes.py --check

SHELL_SCRIPTS := install.sh scripts/*.sh bash/.bashrc \
	hypr/.local/bin/wallpaper-picker color-schemes/.local/bin/color-scheme \
	eww/.config/eww/scripts/*.sh waybar/.config/waybar/scripts/*.sh \
	system/etc/NetworkManager/dispatcher.d/*

lint: ## Run shellcheck over every shell script
	shellcheck -x $(SHELL_SCRIPTS)

test: ## Run the colour scheme builder's tests
	python3 -m pytest -q scripts

check: lint test color-schemes-check ## Everything CI runs
