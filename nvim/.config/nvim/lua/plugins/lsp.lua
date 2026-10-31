-- Language servers through Neovim's built-in client (vim.lsp.config/enable).
-- nvim-lspconfig only supplies the default server definitions (its lsp/
-- directory); per-server overrides live in after/lsp/<server>.lua.
-- Mason installs the server binaries; mason-lspconfig translates the names.
return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      { "mason-org/mason.nvim", opts = {} },
      {
        "mason-org/mason-lspconfig.nvim",
        opts = {
          ensure_installed = { "lua_ls", "basedpyright" },
        },
      },
    },
    config = function()
      vim.lsp.enable({ "lua_ls", "basedpyright" })
      vim.keymap.set("n", "K", vim.lsp.buf.hover, { desc = "LSP hover" })
    end,
  },
}
