-- Example: minimal Neovim config for an on-camera editor session (nvim case).
-- The same ideas apply to any editor: clean chrome, deterministic input,
-- and a stubbed "open browser" side effect.
vim.opt.runtimepath:prepend("/abs/path/to/plugin-under-demo")

vim.o.termguicolors = true
vim.o.number = true
vim.o.signcolumn = "no"
vim.o.laststatus = 2
vim.o.cmdheight = 1
vim.o.ruler = false
vim.o.showcmd = false
vim.o.swapfile = false
vim.o.shortmess = vim.o.shortmess .. "IFW" -- no intro screen / file info noise
vim.o.fillchars = "eob: "                  -- hide ~ on empty lines
vim.o.statusline = " %f %m%=markdown "
vim.cmd.colorscheme("habamax")

vim.api.nvim_create_autocmd("FileType", {
    pattern = "markdown",
    callback = function()
        pcall(vim.treesitter.start) -- pretty highlighting, parsers ship with nvim
        -- keep scripted keystrokes predictable: no auto-bullets, no auto-indent
        vim.opt_local.formatoptions:remove({ "r", "o", "c", "t" })
        vim.opt_local.autoindent = false
    end,
})

-- CRITICAL: don't open the real system browser during the recording.
-- The harness polls this file and points the preview iframe at the URL.
vim.ui.open = function(url)
    vim.fn.writefile({ url }, "/tmp/demo/url.txt")
end
