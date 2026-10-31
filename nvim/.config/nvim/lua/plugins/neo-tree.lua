return {
  "nvim-neo-tree/neo-tree.nvim",
  branch = "v3.x",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-tree/nvim-web-devicons",
    "MunifTanjim/nui.nvim",
  },
  lazy = false, -- neo-tree lazy-loads itself

  ---@module "neo-tree"
  ---@type neotree.Config?
  opts = {},

  keys = {
    { "<C-b>", "<cmd>Neotree<CR>", desc = "Neo-tree: open" },
    { "<C-S-b>", "<cmd>Neotree close filesystem<CR>", desc = "Neo-tree: close" },
  },
}
