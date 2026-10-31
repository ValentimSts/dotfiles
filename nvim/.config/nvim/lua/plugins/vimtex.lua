return {
  "lervag/vimtex",
  lazy = false, -- VimTeX manages its own lazy loading by filetype
  init = function()
    vim.g.vimtex_view_method = "zathura"
  end,
}
