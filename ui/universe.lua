--- fzf-lua picker over the AI universe (ai_stocks_reviewed.json, loaded
--- into DuckDB by db.load_universe). Groups are the five primary buckets,
--- every sub-bucket nested under its parent, and quoted-market regions.
--- Picking one opens a treemap of its members, tiles sized by that
--- security's attributed weight to the bucket.
---
--- Each entry lists its member tickers (dimmed, heaviest exposure first)
--- after the label so typing a ticker (e.g. "NVDA") narrows the list to
--- every group that security belongs to. Tickers must be visible: fzf >=
--- 0.73 restricts matching to what --with-nth shows, so a hidden field
--- would not be searchable. Lines wrap so the matched ticker is on screen,
--- and matching is exact so "aehr" hits AEHR rather than scattered letters
--- inside "autonomous_vehicles".
local M = {}

local SEP = "\t"
local DIM, RESET = "\27[2m", "\27[0m"

local function label(g)
  if g.level == "primary" then
    return string.format("%-32s  %3d  [primary]", g.category, g.count)
  elseif g.level == "sub" then
    return string.format("  %-30s  %3d  %s", g.category, g.count, g.parent or "")
  end
  return string.format("%-32s  %3d  [region]", g.category, g.count)
end

--- @param slot "left"|"right"|nil
function M.pick(slot)
  local ok, fzf = pcall(require, "fzf-lua")
  if not ok then
    vim.notify("security_spread: fzf-lua not installed", vim.log.levels.ERROR)
    return
  end
  local spread = require("custom_plugins.security_spread")

  spread.universe_groups(function(gok, groups)
    if not gok then
      vim.notify("security_spread: " .. tostring(groups), vim.log.levels.ERROR)
      return
    end
    local by_label, labels = {}, {}
    for _, g in ipairs(groups) do
      local l = label(g)
      by_label[l] = g
      labels[#labels + 1] = l .. SEP .. DIM .. table.concat(g.tickers or {}, " ") .. RESET
    end
    fzf.fzf_exec(labels, {
      prompt = "AI universe> ",
      fzf_opts = {
        ["--ansi"] = true,
        ["--delimiter"] = SEP,
        ["--exact"] = true,
        ["--wrap"] = true,
        ["--wrap-sign"] = "      ",
        ["--gap"] = 1,
      },
      actions = {
        ["default"] = function(selected)
          local g = by_label[(selected[1] or ""):match("^[^" .. SEP .. "]*")]
          if not g then
            return
          end
          local win = require("custom_plugins.security_spread.ui.picker").host_win_for_slot(slot)
          spread.show_universe_group(g, { win = win })
        end,
      },
    })
  end)
end

return M
