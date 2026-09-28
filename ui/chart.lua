local M = {}

--- Resamples `closes` to `cols` evenly-spaced points (used for the crosshair
--- readout — the PNG itself plots full-resolution data, this is just for
--- mapping a cursor column back to a price).
--- @param closes number[]
--- @param cols integer
--- @return number[]
local function resample(closes, cols)
  local out = {}
  for i = 1, cols do
    local idx = math.max(1, math.floor((i - 1) / (cols - 1) * (#closes - 1) + 1))
    out[i] = closes[idx]
  end
  return out
end

--- Fetches history for every symbol in parallel and calls back once all
--- have resolved (or errored — errored symbols are just dropped with a
--- warning so one bad symbol doesn't sink the whole overlay).
--- @param symbols string[]
--- @param callback fun(series: table[]) each { symbol, closes }
local function fetch_all(symbols, callback)
  local ss = require("custom_plugins.security_spread")
  local series = {}
  local remaining = #symbols
  for _, symbol in ipairs(symbols) do
    ss.history_yahoo(symbol, function(ok, points)
      remaining = remaining - 1
      if ok and #points > 0 then
        local closes = {}
        for _, p in ipairs(points) do
          closes[#closes + 1] = p.close
        end
        series[#series + 1] = { symbol = symbol, closes = closes }
      else
        vim.notify("security_spread: no history for " .. symbol, vim.log.levels.WARN)
      end
      if remaining == 0 then
        callback(series)
      end
    end)
  end
end

--- @param symbols string[]|string
function M.show(symbols)
  if type(symbols) == "string" then
    symbols = { symbols }
  end

  fetch_all(symbols, function(series)
    if #series == 0 then
      vim.notify("security_spread: no history for any selected symbol", vim.log.levels.ERROR)
      return
    end

    -- Cell-to-pixel is terminal/font dependent; this is a reasonable
    -- default cell size (most monospace fonts land near this) — good
    -- enough since Snacks.image displays at the cell box we request
    -- regardless of the PNG's exact native pixel size.
    local cell_w, cell_h = 8, 16
    local cols = math.min(90, vim.o.columns - 10)
    local chart_rows = 22
    local width_px = cols * cell_w
    local height_px = chart_rows * cell_h

    local image_line = 2 -- image occupies `chart_rows` lines starting here
    local crosshair_line = image_line + chart_rows + 1

    local names = {}
    for _, s in ipairs(series) do
      names[#names + 1] = s.symbol
    end

    local buf_lines = { " overlay: " .. table.concat(names, " / ") }
    for _ = 1, chart_rows do
      buf_lines[#buf_lines + 1] = ""
    end
    buf_lines[crosshair_line] = " move cursor over the chart for values at that column"
    buf_lines[crosshair_line + 1] = ""
    buf_lines[crosshair_line + 2] = " q / <Esc> to close"

    local buf = vim.api.nvim_create_buf(false, true)
    vim.bo[buf].bufhidden = "wipe"
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, buf_lines)
    vim.bo[buf].modifiable = false

    local win_height = #buf_lines
    local win = vim.api.nvim_open_win(buf, true, {
      relative = "editor",
      row = math.floor((vim.o.lines - win_height) / 2),
      col = math.floor((vim.o.columns - cols - 2) / 2),
      width = cols + 1,
      height = win_height,
      style = "minimal",
      border = "rounded",
      title = " history (% change) ",
      title_pos = "center",
      zindex = 100,
    })

    local ok_snacks, snacks_image = pcall(require, "snacks.image")
    local placement = nil
    local tmp_path = nil

    require("custom_plugins.security_spread").render_chart(series, width_px, height_px, function(ok, path_or_err)
      if not ok then
        vim.notify("security_spread: chart render failed: " .. tostring(path_or_err), vim.log.levels.ERROR)
        return
      end
      if not vim.api.nvim_win_is_valid(win) then
        vim.fn.delete(path_or_err) -- window already closed before render finished
        return
      end
      tmp_path = path_or_err

      if not ok_snacks then
        vim.notify("security_spread: snacks.nvim image module not available", vim.log.levels.ERROR)
        return
      end

      placement = snacks_image.placement.new(buf, tmp_path, {
        pos = { image_line, 1 },
        width = cols,
        height = chart_rows,
        inline = true,
      })
    end)

    -- Crosshair: as the cursor moves over the image's rows, show every
    -- series' actual value at that column (real interactivity — the image
    -- is static, but the readout tracks the live cursor position).
    vim.api.nvim_create_autocmd("CursorMoved", {
      buffer = buf,
      callback = function()
        local cursor = vim.api.nvim_win_get_cursor(win)
        local line, byte_col = cursor[1], cursor[2]
        if line < image_line or line > image_line + chart_rows - 1 then
          return
        end
        local sample_col = math.max(1, math.min(cols, byte_col + 1))

        local parts = {}
        for _, s in ipairs(series) do
          local sampled = resample(s.closes, cols)
          parts[#parts + 1] = string.format("%s $%.2f", s.symbol, sampled[sample_col])
        end
        local text = " @ col " .. sample_col .. "   " .. table.concat(parts, "   ")

        vim.bo[buf].modifiable = true
        vim.api.nvim_buf_set_lines(buf, crosshair_line - 1, crosshair_line, false, { text })
        vim.bo[buf].modifiable = false
      end,
    })

    local close = function()
      if placement then
        pcall(function()
          placement:close()
        end)
      end
      if tmp_path then
        vim.fn.delete(tmp_path)
      end
      if vim.api.nvim_win_is_valid(win) then
        vim.api.nvim_win_close(win, true)
      end
    end
    vim.keymap.set("n", "q", close, { buffer = buf, silent = true })
    vim.keymap.set("n", "<Esc>", close, { buffer = buf, silent = true })
  end)
end

return M
