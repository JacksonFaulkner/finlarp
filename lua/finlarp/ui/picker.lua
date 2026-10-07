local M = {}

--- Opens a real split window to host a dashboard (a blank scratch buffer —
--- the treemap tiles float on top of it, `relative = "win"`), and returns
--- its window id. Real split = native resize, <C-w> layout, closes with `q`.
--- @param slot "left"|"right"|nil
function M.host_win_for_slot(slot)
  if slot == "left" then
    vim.cmd("leftabove vsplit")
  elseif slot == "right" then
    vim.cmd("rightbelow vsplit")
  else
    return nil -- fullscreen: no host window, float over the whole editor
  end
  local win = vim.api.nvim_get_current_win()
  local buf = vim.api.nvim_create_buf(false, true)
  vim.bo[buf].bufhidden = "wipe"
  vim.api.nvim_win_set_buf(win, buf)
  return win
end

--- Opens the watchlist-name picker; selecting one opens that watchlist's
--- session, docked per `slot`.
--- @param slot "left"|"right"|"full"|nil
function M.pick(slot)
  local ok, fzf = pcall(require, "fzf-lua")
  if not ok then
    vim.notify("finlarp: fzf-lua not installed", vim.log.levels.ERROR)
    return
  end

  local lists = require("finlarp.ui.watchlists")
  local by_name = {}
  local names = {}
  for _, entry in ipairs(lists) do
    by_name[entry.name] = entry
    names[#names + 1] = entry.name
  end

  fzf.fzf_exec(names, {
    prompt = "Watchlist> ",
    actions = {
      ["default"] = function(selected)
        local entry = by_name[selected[1]]
        if not entry then
          return
        end
        local win = M.host_win_for_slot(slot)
        require("finlarp").show_entry(entry, { win = win })
      end,
    },
  })
end

return M
