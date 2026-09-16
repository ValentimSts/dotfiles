---------------------------------------------------------
--
-- Telescope dotfiles taken/adapted from 'smithbm2316' on GitHub
-- (https://github.com/smithbm2316/dotfiles)
--
---------------------------------------------------------

return {
  'nvim-telescope/telescope.nvim', tag = '0.1.8',
  dependencies = {
    'nvim-lua/plenary.nvim',
    'nvim-tree/nvim-web-devicons',
    'folke/trouble.nvim',
  },
  event = 'VeryLazy',

  config = function() 
    local telescope = require 'telescope'
    local builtin = require 'telescope.builtin'
    local actions = require 'telescope.actions'
    local themes = require 'telescope.themes'
    -- local action_state = require 'telescope.actions.state'
    -- local previewers = require 'telescope.previewers'
    -- local pickers = require 'telescope.pickers'
    -- local sorters = require 'telescope.sorters'
    -- local finders = require 'telescope.finders'
    -- local conf = require('telescope.config').values

    -- files to ignore with `file_ignore_patterns`
    -- if you want to ignore a file with `live_grep`, it needs to go here
    bs.telescope.always_ignored =
      vim.tbl_deep_extend('force', bs.telescope.always_ignored, {
        '%.avi',
        '%.avif',
        '%.db',
        '%.env%..*',
        '%.env',
        '%.flv',
        '%.generated%.d%.ts',
        '%.git/.*',
        '%.heic',
        '%.ico',
        '%.jpeg',
        '%.jpg',
        '%.mkv',
        '%.mov',
        '%.mp3',
        '%.mp4',
        '%.png',
        '%.svg',
        '%.wav',
        '%.webm$',
        '%.webp',
        '%.zip',
        '.obsidian/.*',
        '__snapshots__/.*', -- thuma ichabod
        'deno%.lock',
        'node_modules/.*',
        'package%-lock%.json',
        'pnpm%-lock%.yaml',
        'yarn%.lock',
      })

    bs.telescope.ignored = vim.tbl_deep_extend('force', bs.telescope.ignored, {
      '%.avi',
      '%.avif',
      '%.db',
      '%.env%..*',
      '%.env',
      '%.eot',
      '%.flv',
      '%.generated%.d%.ts',
      '%.git/.*',
      '%.heic',
      '%.ico',
      '%.jpeg',
      '%.jpg',
      '%.mkv',
      '%.mov',
      '%.mp3',
      '%.mp4',
      '%.otf',
      '%.png',
      '%.svg',
      '%.ttf',
      '%.wav',
      '%.webm$',
      '%.webp',
      '%.woff',
      '%.woff2',
      '%.zip',
      '.gitkeep',
      '.obsidian.vimrc',
      '.obsidian/.*',
      '.yarn/.*',
      '__generated__/.*', -- kcrw project
      '__snapshots__/.*', -- thuma ichabod
      '@types/.*', -- thuma ichabod
      'vendor/.*', -- ignore odin vendor directories
      'deno%.lock',
      'generated%-gql/.*', -- inkd project
      'generated/graphql%.tsx', -- scoutus project
      'go%.sum',
      'graphql%.schema%.json',
      'node_modules/.*',
      'package%-lock%.json',
      'pnpm%-lock%.yaml',
      'schema%.json',
      'yarn%.lock',
      'zsh%-abbr/.*',
      'zsh%-autosuggestions/.*',
      'zsh%-completions/.*',
      'zsh%-syntax%-highlighting/.*',
    })

    -- Keymaps
    vim.keymap.set('n', '<leader>ff', builtin.find_files, { desc = 'Telescope find files' })
    vim.keymap.set('n', '<leader>fg', builtin.live_grep, { desc = 'Telescope live grep' })
    vim.keymap.set('n', '<leader>fb', builtin.buffers, { desc = 'Telescope buffers' })
    vim.keymap.set('n', '<leader>fh', builtin.help_tags, { desc = 'Telescope help tags' })
    
    local default_picker_opts = {
      grep_string = {
        prompt_title = 'word under cursor',
      },
      live_grep = {
        file_ignore_patterns = bs.telescope.always_ignored,
      },
      git_commits = {
        selection_strategy = 'row',
        prompt_title = 'git log',
      },
      buffers = {
        show_all_buffers = true,
        attach_mappings = function(_, local_map)
          local_map('n', 'd', actions.delete_buffer)
          local_map('i', '<c-x>', actions.delete_buffer)
          return true
        end,
      },
      git_branches = {
        attach_mappings = function(_, local_map)
          local_map('i', '<c-o>', actions.git_checkout)
          local_map('n', '<c-o>', actions.git_checkout)
          return true
        end,
        selection_strategy = 'row',
      },
      find_files = {
        find_command = { 'fd', '--hidden', '--type', 'f' },
        follow = true,
        hidden = true,
        no_ignore = false,
      },
      lsp_code_actions = themes.get_dropdown(),
      lsp_range_code_actions = themes.get_dropdown(),
    }   

    -- TELESCOPE CONFIG
    telescope.setup {
      pickers = default_picker_opts,
      defaults = {
        vimgrep_arguments = {
          'rg',
          '--color=never',
          '--no-heading',
          '--with-filename',
          '--line-number',
          '--column',
          '--smart-case',
        },
        mappings = {
          n = {
            ['<c-s>'] = actions.select_horizontal,
            ['<c-c>'] = actions.close,
          },
        },
        color_devicons = true,
        prompt_prefix = '🔍 ',
        scroll_strategy = 'cycle',
        sorting_strategy = 'ascending',
        layout_strategy = 'flex',
        file_ignore_patterns = bs.telescope.ignored,
        layout_config = {
          prompt_position = 'top',
          horizontal = {
            mirror = true,
            preview_cutoff = 100,
            preview_width = 0.5,
          },
          vertical = {
            mirror = true,
            preview_cutoff = 0.4,
          },
          flex = {
            flip_columns = 200,
          },
          height = 0.94,
          width = 0.86,
        },
        preview = {
          filesize_limit = 1.0, -- MB
        },
      }, 
    }
  end,
}
