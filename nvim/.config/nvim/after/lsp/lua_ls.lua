-- lua_ls tuned for editing this Neovim config: know the `vim` global and the
-- runtime files, and do not prompt about third-party libraries.
return {
  settings = {
    Lua = {
      runtime = { version = "LuaJIT" },
      diagnostics = { globals = { "vim" } },
      workspace = {
        checkThirdParty = false,
        library = { vim.env.VIMRUNTIME },
      },
    },
  },
}
