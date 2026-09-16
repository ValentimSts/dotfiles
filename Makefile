# Thin wrappers over scripts/. Run `make help` for the list.
PROFILE ?= gnome
SHELL := /usr/bin/env bash

.PHONY: help install stow unstow restow packages export-packages gnome-export gnome-import secrets services lint

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

packages: ## Install pacman, AUR and flatpak packages
	scripts/install-packages.sh

export-packages: ## Refresh packages/*.txt from this machine
	scripts/export-packages.sh

gnome-export: ## Dump dconf settings and extension list into gnome/
	scripts/gnome-export.sh

gnome-import: ## Load gnome/ into dconf and enable extensions
	scripts/gnome-import.sh

secrets: ## Create ~/.config/shell/secrets.sh from the example
	scripts/secrets-init.sh

services: ## Enable systemd services for PROFILE
	scripts/enable-services.sh --profile $(PROFILE)

lint: ## Run shellcheck over all scripts
	shellcheck -x install.sh scripts/*.sh
