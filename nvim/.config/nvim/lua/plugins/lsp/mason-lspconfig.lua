return {
  "williamboman/mason-lspconfig.nvim",

  config = function()
    require("mason-lspconfig").setup({
      ensure_installed = {
        "lua_ls",
        "python_ls"
        -- More LSs
      }
    })
  end
}
