-- nvim-treesitter main branch: it only installs parsers; highlighting and
-- indentation are started per buffer with the built-in vim.treesitter API.
-- Needs the tree-sitter CLI (pacman: tree-sitter-cli) to build parsers.
return {
  "nvim-treesitter/nvim-treesitter",
  branch = "main",
  lazy = false,
  build = ":TSUpdate",
  config = function()
    -- Parsers are built with the tree-sitter CLI; without it every start
    -- would spam failed downloads, so say so once instead.
    if vim.fn.executable("tree-sitter") == 1 then
      require("nvim-treesitter").install({ "lua", "python", "vim", "vimdoc", "query" })
    else
      vim.schedule(function()
        vim.notify("nvim-treesitter: install tree-sitter-cli (pacman) to build parsers", vim.log.levels.WARN)
      end)
    end

    vim.api.nvim_create_autocmd("FileType", {
      group = vim.api.nvim_create_augroup("treesitter-start", { clear = true }),
      callback = function(args)
        -- Only buffers whose language has a parser installed.
        if pcall(vim.treesitter.start, args.buf) then
          vim.bo[args.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
        end
      end,
    })
  end,
}
