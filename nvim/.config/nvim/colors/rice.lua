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
local emphasis = palette.emphasis
palette.emphasis = nil
require('mini.base16').setup({ palette = palette, use_cterm = true })
vim.g.colors_name = 'rice' -- after setup: mini.base16 clears it while applying the palette

-- A scheme without hues has only ink and weight to tell syntax apart.
if emphasis then
  local function add(attribute, groups)
    for _, group in ipairs(groups) do
      local hl = vim.api.nvim_get_hl(0, { name = group, link = false })
      hl[attribute] = true
      vim.api.nvim_set_hl(0, group, hl)
    end
  end
  add('bold', { 'Keyword', 'Conditional', 'Repeat', 'Statement', 'Exception', 'Label', '@keyword.return', 'Title', 'DiagnosticError' })
  add('italic', { 'Comment' })
end
