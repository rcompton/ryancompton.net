-- initial.lua -- a decorated initial for florilegium (LuaLaTeX only).
-- Copyright (c) 2026 Kevin Raymond. MIT License: see LICENSE or florilegium.sty.
--
-- A square tile at the start of a paragraph: the letter, its outline read from
-- an OpenType font and painted like a petal; a vine that winds over and under
-- the letter's strokes, as in an interlaced manuscript initial; leaves where
-- they fit and small flowers in the largest gaps; a double frame, like a tile.
-- Drawn in a local frame of centimeters, [0,S] x [0,S], under the current ink
-- transform.

local ink = require("ink")
local flora = require("flora")
local M = {}

local sqrt, cos, sin, pi, floor, max, min, abs, atan = math.sqrt, math.cos, math.sin, math.pi, math.floor, math.max, math.min, math.abs, math.atan
local tone, white = ink.tone, ink.white
local rad = pi / 180
local function lerp(a, b, t) return a + (b - a) * t end
local function dist(ax, ay, bx, by) local dx, dy = ax - bx, ay - by return sqrt(dx * dx + dy * dy) end

-- ---------------------------------------------------------------- outlines
-- luaotfload's reader returns each glyph as segments in font units:
-- {x, y, "m"}, {x, y, "l"}, {x1, y1, x2, y2, x3, y3, "c"}, {x1, y1, x2, y2, "q"}
local cache = {}
local function font_glyphs(file)
  if cache[file] then return cache[file] end
  local path = kpse.find_file(file, "opentype fonts") or kpse.find_file(file, "truetype fonts")
  if not path then return nil end
  local shapes = fonts.handlers.otf.readers.loadshapes(path)
  local byuni = {}
  for _, gl in pairs(shapes.glyphs or {}) do
    if type(gl.unicode) == "number" and not byuni[gl.unicode] then byuni[gl.unicode] = gl end
  end
  cache[file] = { units = shapes.units or 1000, byuni = byuni }
  return cache[file]
end

-- the contours of one character, as path commands and as flattened polygons,
-- scaled to fit a box of height h and width w (cm) centered at (cx, cy)
local function contours(file, char, cx, cy, h, w)
  local f = font_glyphs(file)
  if not f then return nil, "font not found: " .. file end
  local gl = f.byuni[utf8.codepoint(char)]
  if not gl or not gl.segments then return nil, "no outline for '" .. char .. "' in " .. file end
  local bb = gl.boundingbox
  local k = min(h / (bb[4] - bb[2]), w / (bb[3] - bb[1]))
  local ox, oy = cx - k * (bb[1] + bb[3]) / 2, cy - k * (bb[2] + bb[4]) / 2
  local function P(x, y) return ox + k * x, oy + k * y end
  local out, cur, lx, ly = {}, nil, 0, 0
  for _, sg in ipairs(gl.segments) do
    local op = sg[#sg]
    if op == "m" then
      cur = { ops = {}, poly = {} }
      out[#out + 1] = cur
      lx, ly = P(sg[1], sg[2])
      cur.ops[1] = { "m", lx, ly } cur.poly[1] = { lx, ly }
    elseif op == "l" and cur then
      lx, ly = P(sg[1], sg[2])
      cur.ops[#cur.ops + 1] = { "l", lx, ly } cur.poly[#cur.poly + 1] = { lx, ly }
    elseif (op == "c" or op == "q") and cur then
      local x1, y1, x2, y2, x3, y3
      if op == "c" then
        x1, y1 = P(sg[1], sg[2]) x2, y2 = P(sg[3], sg[4]) x3, y3 = P(sg[5], sg[6])
      else                                     -- quadratic as cubic
        local qx, qy = P(sg[1], sg[2])
        x3, y3 = P(sg[3], sg[4])
        x1, y1 = lx + 2 / 3 * (qx - lx), ly + 2 / 3 * (qy - ly)
        x2, y2 = x3 + 2 / 3 * (qx - x3), y3 + 2 / 3 * (qy - y3)
      end
      cur.ops[#cur.ops + 1] = { "c", x1, y1, x2, y2, x3, y3 }
      local f3 = ink.bezier3(lx, ly, x1, y1, x2, y2, x3, y3)
      for i = 1, 8 do local x, y = f3(i / 8) cur.poly[#cur.poly + 1] = { x, y } end
      lx, ly = x3, y3
    end
  end
  return out
end

local function trace(cs)
  for _, c in ipairs(cs) do
    for _, o in ipairs(c.ops) do
      if o[1] == "m" then ink.moveto(o[2], o[3])
      elseif o[1] == "l" then ink.lineto(o[2], o[3])
      else ink.curveto(o[2], o[3], o[4], o[5], o[6], o[7]) end
    end
    ink.close()
  end
end

-- even-odd point in the letter
local function inside(cs, x, y)
  local c = false
  for _, ct in ipairs(cs) do
    local p, n = ct.poly, #ct.poly
    local j = n
    for i = 1, n do
      local xi, yi, xj, yj = p[i][1], p[i][2], p[j][1], p[j][2]
      if (yi > y) ~= (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi then c = not c end
      j = i
    end
  end
  return c
end

-- ---------------------------------------------------------------- the tile
-- S: side (cm); letter: one character; o.font: an OpenType file (Latin Modern
-- Roman Bold by default, the OpenType twin of Computer Modern)
function M.draw(rng, S, letter, o)
  o = o or {}
  local m = 0.07 * S                           -- the frame's inset
  local cs, err = contours(o.font or "lmroman10-bold.otf", letter, S * 0.5, S * 0.47, S * 0.66, S * 0.7)
  if not cs then return nil, err end
  -- free space: a grid of the distance to the letter and the frame
  local N = 36
  local cell = S / N
  local blocked, freecells = {}, {}
  for i = 0, N - 1 do
    for j = 0, N - 1 do
      local x, y = (i + 0.5) * cell, (j + 0.5) * cell
      if inside(cs, x, y) then blocked[#blocked + 1] = { x, y } else freecells[#freecells + 1] = { x, y } end
    end
  end
  local function clearance(x, y)
    local d = min(x - m, S - m - x, y - m, S - m - y)
    for _, b in ipairs(blocked) do
      local e = dist(x, y, b[1], b[2]) - cell * 0.7
      if e < d then d = e end
    end
    return d
  end

  -- the ground: a pale glaze and a double frame
  ink.layer(1)
  ink.poly({ { 0, 0 }, { S, 0 }, { S, S }, { 0, S } }, true) ink.clip()
    ink.flood(tone(0.975), 0, 0, S, S)
    flora.mottle(rng, 0, 0, S, S, 6, S * 0.2, 0.93, 1.0, 0)
  ink.unclip()
  ink.poly({ { 0, 0 }, { S, 0 }, { S, S }, { 0, S } }, true) ink.stroke(tone(0.1), 0.8)
  ink.poly({ { m * 0.5, m * 0.5 }, { S - m * 0.5, m * 0.5 }, { S - m * 0.5, S - m * 0.5 }, { m * 0.5, S - m * 0.5 } }, true)
  ink.stroke(tone(0.15), 0.3, 0.8)

  -- the vine: from the lower-left corner up across the letter to the upper right
  local f = ink.fbm1(rng, 2)
  local ctrl = {
    { m * 1.2, m * 1.2 }, { S * rng.range(0.14, 0.22), S * rng.range(0.3, 0.4) }, { S * rng.range(0.32, 0.42), S * rng.range(0.5, 0.58) },
    { S * rng.range(0.58, 0.68), S * rng.range(0.42, 0.52) }, { S * rng.range(0.74, 0.82), S * rng.range(0.62, 0.72) }, { S - m * 1.6, S - m * 1.4 } }
  local pts = ink.catmull(ctrl, 14)
  for i, p in ipairs(pts) do local u = (i - 1) / (#pts - 1) p[2] = p[2] + 0.03 * S * f(u * 6) end
  local w0, w1 = 0.026 * S, 0.01 * S
  local function width(i) return lerp(w0, w1, (i - 1) / (#pts - 1)) end
  ink.layer(2)
  flora.stem(pts, w0, w1)
  -- where it crosses the letter, it goes over and under in turn
  local runs, run = {}, nil
  for i, p in ipairs(pts) do
    if inside(cs, p[1], p[2]) then
      if not run then run = { i, i } runs[#runs + 1] = run else run[2] = i end
    else run = nil end
  end
  -- the strands that pass over: drawn again on top of the letter, inside its
  -- outline only, with a thin halo of paper that parts them from the letter
  local over = rng.chance(0.5)
  for _, r in ipairs(runs) do
    if over then
      local a, b = max(1, r[1] - 2), min(#pts, r[2] + 2)
      local seg = {}
      for i = a, b do seg[#seg + 1] = pts[i] end
      ink.layer(4)
      trace(cs) ink.clip()
        ink.smooth(seg, false) ink.stroke(ink.paper, (width(a) + width(b)) / 2 * ink.unit() * ink.CM + 1.0)
        flora.stem(seg, width(a), width(b))
      ink.unclip()
    end
    over = not over
  end
  -- a bud at its tip
  do
    local e, q = pts[#pts], pts[#pts - 3]
    ink.layer(5)
    ink.push() ink.translate(e[1], e[2]) ink.rotate(atan(e[2] - q[2], e[1] - q[1]) / rad - 90)
    flora.bud(rng, 0.13 * S)
    ink.pop()
  end

  -- the letter: wash, granulation, pooled edges, light lifted out
  local t0 = o.tone or rng.range(0.16, 0.22)
  ink.layer(3)
  trace(cs) ink.fill(tone(t0))
  trace(cs) ink.clip()
    flora.mottle(rng, 0, 0, S, S, 22, S * 0.06, t0 - 0.12, t0 + 0.2, 20)
    for k = 1, 9 do
      local x = S * (0.15 + 0.7 * (k - 0.5) / 9) + rng.sym(0.02 * S)
      local y0, y1 = S * rng.range(0.1, 0.25), S * rng.range(0.72, 0.9)
      flora.streak3(x, y0, x + 0.02 * S, lerp(y0, y1, 0.35), x - 0.02 * S, lerp(y0, y1, 0.7), x + rng.sym(0.03 * S), y1,
        0.018 * S, 0.003 * S, white, rng.range(0.25, 0.45))
    end
    trace(cs) ink.stroke(tone(0.04), 0.07 * S * ink.unit() * ink.CM, 0.45, true)
  ink.unclip()
  trace(cs) ink.stroke(tone(0.04), 0.35, 0.7)

  -- leaves along the vine where they fit, alternating sides
  ink.layer(4)
  local s, acc, side = 0, S * rng.range(0.08, 0.14), 1
  for i = 2, #pts - 3 do
    s = s + dist(pts[i][1], pts[i][2], pts[i - 1][1], pts[i - 1][2])
    if s >= acc then
      acc = acc + S * rng.range(0.11, 0.16)
      side = -side
      local tx, ty = pts[i + 1][1] - pts[i - 1][1], pts[i + 1][2] - pts[i - 1][2]
      local a = atan(ty, tx) / rad + side * rng.range(40, 60)
      local L = S * rng.range(0.16, 0.22)
      local ok = true
      for _, u in ipairs({ 0.35, 0.65, 0.95 }) do
        local x, y = pts[i][1] + L * u * cos(a * rad), pts[i][2] + L * u * sin(a * rad)
        if inside(cs, x, y) or clearance(x, y) < 0.03 * S then ok = false end
      end
      if ok then
        ink.push() ink.translate(pts[i][1], pts[i][2]) ink.rotate(a - 90) ink.scale(L)
        flora.leaflet(rng, { bend = -side * 0.2 })
        ink.pop()
      end
    end
  end

  -- flowers in the largest gaps: a blossom, and florets on hairlines from the vine
  ink.layer(5)
  local spots = {}
  for _, c in ipairs(freecells) do
    local cl = clearance(c[1], c[2])
    if cl > 0.06 * S then spots[#spots + 1] = { c[1], c[2], cl } end
  end
  table.sort(spots, function(a, b) return a[3] > b[3] end)
  local placed = {}
  local nb = 0
  for _, sp in ipairs(spots) do
    if nb >= 4 then break end
    local far = true
    for _, p in ipairs(placed) do if dist(sp[1], sp[2], p[1], p[2]) < p[3] + sp[3] + 0.04 * S then far = false end end
    if far then
      nb = nb + 1
      local r = min(sp[3] * 0.85, 0.12 * S)
      placed[#placed + 1] = { sp[1], sp[2], r }
      -- a hairline stalk back to the vine, if the vine is near
      local best, bp = math.huge, nil
      for _, p in ipairs(pts) do local d = dist(p[1], p[2], sp[1], sp[2]) if d < best then best, bp = d, p end end
      if bp and best < 0.3 * S then
        ink.layer(2)
        ink.moveto(bp[1], bp[2]) ink.curveto(lerp(bp[1], sp[1], 0.3), lerp(bp[2], sp[2], 0.1) + 0.03 * S, lerp(bp[1], sp[1], 0.7), sp[2] - 0.02 * S, sp[1], sp[2])
        ink.stroke(tone(0.12), 0.35)
        ink.layer(5)
      end
      ink.push() ink.translate(sp[1], sp[2])
      if r > 0.07 * S and nb <= 2 then flora.blossom(rng, r) else flora.floret(rng, r * 0.8, { star = rng.chance(0.5) }) end
      ink.pop()
    end
  end
  -- a copper sparkle in a corner
  ink.layer(6)
  ink.push() ink.translate(S - m * 2.2, m * 2.2) flora.sparkle(rng, 0.045 * S) ink.pop()
  return true
end

return M
