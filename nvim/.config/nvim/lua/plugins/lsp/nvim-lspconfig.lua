return {
  "neovim/nvim-lspconfig",

  config = function()
    local lspconfig = require("lspconfig")
    
    -- Setup all language servers
    lspconfig.lua_ls.setup({})
    lspconfig.python_ls.setup({})

    vim.keymap.set('n', 'K', vim.lsp.buf.hover, {})
  end
}
