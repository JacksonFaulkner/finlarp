-- Squarified treemap layout (Bruls, Huizing, van Wijk).
-- Port of the reference algorithm used by the `squarify` PyPI package.
local M = {}

local function sum(sizes)
  local s = 0
  for _, v in ipairs(sizes) do
    s = s + v
  end
  return s
end

function M.normalize_sizes(sizes, dx, dy)
  local total_size = sum(sizes)
  local total_area = dx * dy
  local out = {}
  for i, s in ipairs(sizes) do
    out[i] = s * total_area / total_size
  end
  return out
end

local function layoutrow(sizes, x, y, dx, dy)
  local covered_area = sum(sizes)
  local width = covered_area / dy
  local rects = {}
  local cy = y
  for _, s in ipairs(sizes) do
    local h = s / width
    rects[#rects + 1] = { x = x, y = cy, dx = width, dy = h }
    cy = cy + h
  end
  return rects
end

local function layoutcol(sizes, x, y, dx, dy)
  local covered_area = sum(sizes)
  local height = covered_area / dx
  local rects = {}
  local cx = x
  for _, s in ipairs(sizes) do
    local w = s / height
    rects[#rects + 1] = { x = cx, y = y, dx = w, dy = height }
    cx = cx + w
  end
  return rects
end

local function layout(sizes, x, y, dx, dy)
  if dx >= dy then
    return layoutrow(sizes, x, y, dx, dy)
  else
    return layoutcol(sizes, x, y, dx, dy)
  end
end

local function leftover(sizes, x, y, dx, dy)
  local covered_area = sum(sizes)
  if dx >= dy then
    local width = covered_area / dy
    return x + width, y, dx - width, dy
  else
    local height = covered_area / dx
    return x, y + height, dx, dy - height
  end
end

local function worst_ratio(sizes, x, y, dx, dy)
  local worst = 0
  for _, rect in ipairs(layout(sizes, x, y, dx, dy)) do
    local ratio = math.max(rect.dx / rect.dy, rect.dy / rect.dx)
    if ratio > worst then
      worst = ratio
    end
  end
  return worst
end

local function slice(t, from, to)
  local out = {}
  for i = from, to do
    out[#out + 1] = t[i]
  end
  return out
end

--- @param sizes number[] pre-normalized areas, sorted descending
--- @return table[] rects in the same order as `sizes`, each {x,y,dx,dy}
function M.squarify(sizes, x, y, dx, dy)
  if #sizes == 0 then
    return {}
  end
  if #sizes == 1 then
    return layout(sizes, x, y, dx, dy)
  end

  local i = 1
  while i < #sizes and worst_ratio(slice(sizes, 1, i), x, y, dx, dy)
      >= worst_ratio(slice(sizes, 1, i + 1), x, y, dx, dy) do
    i = i + 1
  end

  local current = slice(sizes, 1, i)
  local remaining = slice(sizes, i + 1, #sizes)
  local lx, ly, ldx, ldy = leftover(current, x, y, dx, dy)

  local rects = layout(current, x, y, dx, dy)
  if #remaining > 0 then
    vim.list_extend(rects, M.squarify(remaining, lx, ly, ldx, ldy))
  end
  return rects
end

--- Convenience wrapper: sorts `items` by `size_fn` descending, normalizes
--- areas to the pixel/cell rect (x, y, dx, dy), and returns
--- { item = item, x, y, dx, dy } for each, rounded to integer cell bounds.
--- @param items table[]
--- @param size_fn fun(item: table): number
function M.layout_items(items, size_fn, x, y, dx, dy)
  local sorted = vim.deepcopy(items)
  table.sort(sorted, function(a, b)
    return size_fn(a) > size_fn(b)
  end)

  local sizes = {}
  for i, it in ipairs(sorted) do
    sizes[i] = size_fn(it)
  end

  local norm = M.normalize_sizes(sizes, dx, dy)
  local rects = M.squarify(norm, x, y, dx, dy)

  local out = {}
  for i, r in ipairs(rects) do
    local x1 = math.floor(r.x + 0.5)
    local y1 = math.floor(r.y + 0.5)
    local x2 = math.floor(r.x + r.dx + 0.5)
    local y2 = math.floor(r.y + r.dy + 0.5)
    out[i] = {
      item = sorted[i],
      x = x1,
      y = y1,
      w = math.max(1, x2 - x1),
      h = math.max(1, y2 - y1),
    }
  end
  return out
end

return M
