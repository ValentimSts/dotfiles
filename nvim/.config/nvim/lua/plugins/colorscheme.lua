return {
  -- { 'sainnhe/everforest' },
  'savq/melange-nvim',
  -- 'xero/miasma.nvim',
  lazy = false,
  priority = 1000,

  config = function()
    local background_to_colorscheme = {
      light = 'everforest',
      dark = 'melange',
      -- dark = 'miasma',
    }
    
    vim.opt.background = 'dark'
    vim.cmd(
      'colorscheme '
        .. background_to_colorscheme[vim.opt.background:get() or 'dark']
    )
    vim.opt.termguicolors = true

    vim.keymap.set('n', '<leader>tt', function()
      local new_background = vim.opt.background:get() == 'dark' and 'light'
        or 'dark'
      vim.opt.background = new_background
      vim.cmd('colorscheme ' .. background_to_colorscheme[new_background])
    end, { desc = 'Toggle colorscheme change' })
  end
}
