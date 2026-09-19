-- Shared per-slot colors for multi-symbol selection/overlay (max 4: see
-- window.lua's MAX_SELECTED). Same slot index always means the same color,
-- from tile border highlight through to the overlay chart line.
local M = {}

M.SERIES = {
  { hl = "SecuritySpreadSeries1", hex = "#7aa2f7", marker = "●" },
  { hl = "SecuritySpreadSeries2", hex = "#e6c265", marker = "▲" },
  { hl = "SecuritySpreadSeries3", hex = "#c678dd", marker = "■" },
  { hl = "SecuritySpreadSeries4", hex = "#56b6c2", marker = "♦" },
}

function M.ensure_highlights()
  for _, s in ipairs(M.SERIES) do
    vim.api.nvim_set_hl(0, s.hl, { fg = s.hex, bold = true, default = true })
  end
end

return M
