-- "rice": the desktop's active colour scheme, applied through mini.base16.
-- The palette is ports/<scheme>/<dark|light>/nvim.lua, reached through the
-- ~/.local/state/color-schemes/scheme symlink that `color-scheme set` manages;
-- the variant follows 'background'.
local mode = vim.o.background == 'light' and 'light' or 'dark'
local path = vim.fn.expand('~/.local/state/color-schemes/scheme/' .. mode .. '/nvim.lua')
local ok, palette = pcall(dofile, path)
if not ok then
  vim.notify('rice: no colour scheme at ' .. path .. ' (run: color-scheme set <scheme>)', vim.log.levels.WARN)
  return
end
require('mini.base16').setup({ palette = palette, use_cterm = true })
vim.g.colors_name = 'rice' -- after setup: mini.base16 clears it while applying the palette
