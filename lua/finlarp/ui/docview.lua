--- Open the document a number came from, inside nvim (views/docview.py
--- fetches + caches + converts it). SEC HTML becomes markdown with clean
--- tables and its images drawn inline by snacks.image; PDFs and images are
--- drawn by snacks.image directly. The quote (from a dossier/search link's
--- #:~:text= fragment, or passed explicitly) is jumped to and highlighted.
---
--- In the viewer tab:
---   q       close the tab
---   gx      open the original URL in the browser
---   n / N   next / previous match of the quote
local M = {}

local plugin_dir = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":h:h:h:h")
local python = plugin_dir .. "/.venv/bin/python"
local script = plugin_dir .. "/views/docview.py"

local HL = "SecuritySpreadQuote"
vim.api.nvim_set_hl(0, HL, { default = true, link = "Search" })

--- Vim regex (very nomagic) matching the quote's opening words, tolerant of
--- markdown escapes and whitespace differences.
local function quote_pattern(quote)
  local words = {}
  for w in quote:gsub("^[%s•·%-]+", ""):gmatch("%S+") do
    words[#words + 1] = vim.fn.escape(w, "\\/")
    if #words == 6 then
      break
    end
  end
  if #words == 0 then
    return nil
  end
  -- \V literal, \_s\+ = any whitespace incl. newline, \\\? = optional backslash escape
  return "\\c\\V" .. table.concat(words, "\\_s\\+"):gsub("%$", "\\\\\\?$")
end

local function show(res, quote)
  vim.cmd("tabnew")
  local win = vim.api.nvim_get_current_win()
  vim.cmd("edit " .. vim.fn.fnameescape(res.path))
  local buf = vim.api.nvim_get_current_buf()
  vim.bo[buf].modifiable = res.kind == "md" or res.kind == "text"
  vim.bo[buf].readonly = true
  vim.bo[buf].bufhidden = "wipe"
  vim.api.nvim_buf_set_var(buf, "finlarp_url", res.url)

  local ok_snacks, snacks_image = pcall(require, "snacks.image")
  if res.kind == "pdf" or res.kind == "image" then
    if ok_snacks then
      snacks_image.buf.attach(buf, { src = res.path })
    else
      vim.notify("finlarp: snacks.image unavailable, can't render " .. res.kind, vim.log.levels.WARN)
    end
    if res.kind == "pdf" and res.text_path then
      -- searchable text version alongside the rendered pages
      vim.cmd("vsplit " .. vim.fn.fnameescape(res.text_path))
      buf = vim.api.nvim_get_current_buf()
      vim.bo[buf].readonly = true
    end
  elseif res.kind == "md" then
    vim.bo[buf].filetype = "markdown"
    vim.wo[win].wrap = true
    vim.wo[win].linebreak = true
    vim.wo[win].conceallevel = 2
    if ok_snacks then
      snacks_image.doc.attach(buf)
    end
  end

  local function map(lhs, fn, desc)
    vim.keymap.set("n", lhs, fn, { buffer = buf, desc = desc, nowait = true })
  end
  map("q", "<cmd>tabclose<cr>", "close document")
  map("gx", function()
    vim.ui.open(res.index_url or res.url)
  end, "open original in browser")

  if res.line then
    pcall(vim.api.nvim_win_set_cursor, 0, { res.line, 0 })
    vim.cmd("normal! zz")
  end
  local pat = quote and quote_pattern(quote)
  if pat then
    vim.fn.matchadd(HL, pat, 20)
    vim.fn.setreg("/", pat) -- n / N step through matches
    vim.o.hlsearch = true
  end
  vim.notify(("%s%s"):format(res.title or "document", res.line and "" or (quote and "  (quote not found)" or "")))
end

--- @param url string source URL (may carry a #:~:text= quote fragment)
--- @param quote string|nil text to jump to; defaults to the URL fragment
function M.open(url, quote)
  if not url or url == "" then
    return
  end
  if not quote then
    local frag = url:match("#:~:text=([^&,]+)")
    quote = frag and frag:gsub("%%(%x%x)", function(h)
      return string.char(tonumber(h, 16))
    end)
  end
  local args = { python, script, url, "--json" }
  if quote then
    vim.list_extend(args, { "--quote", quote })
  end
  vim.notify("finlarp: opening source…")
  vim.system(args, { text = true }, function(r)
    vim.schedule(function()
      if r.code ~= 0 then
        vim.notify("finlarp: docview failed: " .. (r.stderr or ""):sub(-300), vim.log.levels.ERROR)
        return
      end
      local ok, res = pcall(vim.json.decode, r.stdout, { luanil = { object = true, array = true } })
      if not ok then
        vim.notify("finlarp: bad docview output", vim.log.levels.ERROR)
        return
      end
      show(res, quote)
    end)
  end)
end

return M
