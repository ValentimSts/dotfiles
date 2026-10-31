-- "rice" (colors/rice.lua) follows the desktop colour scheme chosen with
-- `color-scheme set`; the variant comes from 'background'.
return {
  "nvim-mini/mini.base16",
  lazy = false,
  priority = 1000,

  config = function()
    -- Start in the mode the desktop is in: the switcher's "active" symlink
    -- ends in dark or light.
    local active = vim.uv.fs_readlink(vim.fn.expand("~/.local/state/color-schemes/active"))
    vim.opt.background = (active and active:match("/light$")) and "light" or "dark"
    vim.cmd.colorscheme("rice")

    vim.keymap.set("n", "<leader>tt", function()
      vim.opt.background = vim.opt.background:get() == "dark" and "light" or "dark"
      vim.cmd.colorscheme("rice")
    end, { desc = "Toggle light / dark" })
  end,
}
