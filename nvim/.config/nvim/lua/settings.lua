local opt = vim.opt

opt.number = true

opt.expandtab = true
opt.tabstop = 2
opt.softtabstop = 2
opt.shiftwidth = 2

-- Yank and paste go through the system clipboard (wl-copy on Wayland).
opt.clipboard = "unnamedplus"

-- Must be set before a colorscheme is applied.
opt.termguicolors = true
