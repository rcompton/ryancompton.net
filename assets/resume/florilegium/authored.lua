-- authored.lua -- the authored composition of florilegium.
-- Copyright (c) 2026 Kevin Raymond. MIT License: see LICENSE or florilegium.sty.
--
-- Everything here is placed by hand, for A4 with a 68 mm left margin (the
-- margin column is x in [0.3, 6.4] cm, the page 29.7 cm tall): three stems
-- through hand-picked control points, leaves at chosen fractions of their
-- length, and motifs at chosen points, each joined to a chosen stem by a
-- branch. Only the parameters are sampled (every petal, lobe and vein, and a
-- jitter of a millimeter or two on the control points), so every page gets
-- the same garden, differently painted. The grown composition (grow.lua)
-- uses the same primitives and the same motif table.

local ink = require("ink")
local grow = require("grow")
local M = {}

local sqrt, cos, sin, atan, pi, max, min, floor = math.sqrt, math.cos, math.sin, math.atan, math.pi, math.max, math.min, math.floor
local rad = pi / 180
local function norm(x, y) local L = sqrt(x * x + y * y) if L < 1e-9 then return 0, 1 end return x / L, y / L end
local function deg(x, y) return atan(y, x) / rad end
local LY = grow.layers

-- ---------------------------------------------------------------- the score
local ROOT = { 1.35, 0.75 }

-- stems: control points (cm), base and tip width, what grows at the tip
local STEMS = {
  A = { pts = { { 1.35, 0.75 }, { 2.3, 3.2 }, { 1.7, 6.6 }, { 2.9, 10.2 }, { 2.1, 13.8 }, { 3.2, 17.6 }, { 2.3, 21.2 }, { 2.9, 24.4 }, { 2.7, 25.6 } },
        w = { 0.085, 0.03 }, tip = { "flower", 1.7, 90 } },
  B = { pts = { { 1.55, 0.75 }, { 3.1, 4.2 }, { 3.7, 8.3 }, { 2.7, 12.2 }, { 3.9, 15.8 }, { 4.4, 18.4 } },
        w = { 0.065, 0.028 }, tip = { "lily", 1.15, 70 } },
  C = { pts = { { 1.15, 0.75 }, { 0.95, 3.6 }, { 2.1, 7.3 }, { 1.3, 10.6 }, { 1.4, 12.0 } },
        w = { 0.06, 0.028 }, tip = { "flower", 0.95, 90 } },
}

-- leaves at the nodes: stem, fraction of its length, side (+1 left), length, lobed
local LEAVES = {
  { "A", 0.08, -1, 2.3, true }, { "A", 0.20, 1, 2.2, false }, { "A", 0.33, -1, 2.0, true }, { "A", 0.47, 1, 1.9, true },
  { "A", 0.60, -1, 1.8, false }, { "A", 0.72, 1, 1.6, true }, { "A", 0.84, -1, 1.4, false },
  { "B", 0.15, 1, 2.1, true }, { "B", 0.33, -1, 1.9, false }, { "B", 0.52, 1, 1.8, true }, { "B", 0.72, -1, 1.5, true },
  { "C", 0.22, 1, 1.8, false }, { "C", 0.46, -1, 1.7, true }, { "C", 0.70, 1, 1.4, false },
}

-- motifs on branches: stem, fraction where the branch leaves, target center (cm), motif, size
local BRANCHES = {
  { "A", 0.90, 0.95, 27.9, "sprig", 1.6 },
  { "A", 0.95, 4.75, 24.9, "bud", 0.7 },
  { "A", 0.86, 4.85, 23.1, "flower", 1.0 },
  { "A", 0.78, 0.95, 22.4, "umbel", 1.3 },
  { "A", 0.70, 0.9, 19.3, "blossoms", 0.75 },
  { "A", 0.74, 5.35, 21.4, "blossoms", 0.65 },
  { "B", 0.86, 5.55, 16.6, "cyme", 1.9 },
  { "A", 0.55, 0.8, 16.0, "bud", 0.7 },
  { "C", 0.95, 0.75, 14.6, "cyme", 1.5 },
  { "A", 0.60, 5.25, 13.4, "blossoms", 0.8 },
  { "C", 0.55, 0.65, 11.4, "bud", 0.6 },
  { "B", 0.45, 5.35, 10.6, "umbel", 1.4 },
  { "C", 0.62, 0.75, 9.0, "bells", 0.9 },
  { "B", 0.28, 5.2, 6.6, "flower", 1.05 },
  { "C", 0.30, 0.7, 5.6, "sprig", 2.0 },
  { "A", 0.22, 4.7, 3.2, "cyme", 1.6 },
  { "B", 0.62, 5.6, 12.0, "tendril", 0.4 },
  { "A", 0.40, 1.0, 13.2, "tendril", 0.35 },
  { "A", 0.97, 3.9, 28.3, "cyme", 1.2 },
  { "A", 0.93, 5.25, 25.4, "blossoms", 0.6 },
  { "A", 0.82, 1.0, 24.7, "leaf", 1.4 },
  { "B", 0.80, 5.7, 19.9, "bud", 0.6 },
  { "B", 0.64, 5.05, 14.9, "leaf", 1.4 },
  { "B", 0.38, 5.35, 8.8, "cyme", 1.4 },
  { "C", 0.50, 0.75, 7.4, "blossoms", 0.6 },
  { "A", 0.10, 0.85, 3.1, "leaf", 1.5 },
  { "B", 0.16, 5.6, 4.4, "bud", 0.6 },
  { "C", 0.85, 2.6, 11.5, "bud", 0.55 },
}

local GHOSTS = { { 3.4, 5.4, 1.5 }, { 2.7, 16.9, 1.25 } }
-- visitors: kind, x, y (cm), size, heading (degrees); the snail: stem, fraction, side
local VISITORS = { { "butterfly", 4.3, 20.6, 1.3, 100 }, { "bee", 1.6, 26.6, 0.75, 30 } }
local SNAIL = { "C", 0.35, 1, 0.8 }
local ACCENTS = { { "rosette", 0.45, 4.2 }, { "sparkle", 0.5, 9.9 }, { "sparkle", 0.45, 18.3 }, { "rosette", 0.5, 24.3 }, { "sparkle", 5.9, 1.6 } }

-- the footer: the stem runs from the root to this fraction of the text width;
-- motifs along it: x (cm), motif, size
local FOOT_END = 0.45
local FOOT = { { 3.6, "cyme", 1.1 }, { 5.3, "blossoms", 0.5 }, { 7.6, "cyme", 1.0 }, { 9.6, "blossoms", 0.42 } }

-- ---------------------------------------------------------------- drawing
-- points along a polyline at a fraction of its length, with the unit tangent
local function at(pts, f)
  local s, tot = ink.arclen(pts)
  local want = f * tot
  for i = 2, #pts do
    if s[i] >= want then
      local tx, ty = norm(pts[i][1] - pts[i - 1][1], pts[i][2] - pts[i - 1][2])
      return pts[i][1], pts[i][2], tx, ty, i
    end
  end
  local n = #pts
  local tx, ty = norm(pts[n][1] - pts[n - 1][1], pts[n][2] - pts[n - 1][2])
  return pts[n][1], pts[n][2], tx, ty, n
end

function M.page(g)
  local rng = ink.rng(g.seed * 7919 + 17)
  local jit = rng.fork()
  local F, own = grow.theme(g.theme)           -- the primitives: flora, or a theme's
  if own then return own(g, grow) end          -- a theme with a composition of its own
  ink.set_transform(ink.page_transform(g.mirror and g.pw))
  local function place(layer, x, y, a, fn)
    ink.layer(layer)
    ink.push() ink.translate(x, y) ink.rotate(a - 90) fn() ink.pop()
  end

  -- stems
  local stems = {}
  for _, name in ipairs({ "A", "B", "C" }) do            -- a fixed order: pairs() is not
    local st = STEMS[name]
    local cp = {}
    for i, p in ipairs(st.pts) do cp[i] = { p[1] + (i > 1 and jit.sym(0.12) or 0), p[2] + (i > 1 and jit.sym(0.12) or 0) } end
    stems[name] = ink.catmull(cp, 10)
  end
  ink.layer(LY.stem)
  for _, name in ipairs({ "C", "B", "A" }) do
    F.stem(stems[name], STEMS[name].w[1], STEMS[name].w[2])
  end
  -- the scroll at the root
  do
    local pts = {}
    for i = 0, 40 do
      local t = i / 40
      local a = pi * 0.5 + t * 1.4 * 2 * pi
      local r = 0.55 * (1 - 0.85 * t) ^ 1.3
      pts[#pts + 1] = { ROOT[1] - 0.55 - r * cos(a), ROOT[2] + 0.05 + r * sin(a) }
    end
    F.stem(pts, 0.06, 0.012)
  end
  -- footer stem
  local fx1 = g.textleft + (g.textright - g.textleft) * FOOT_END
  local foot = {}
  do
    local f = ink.fbm1(jit, 2)
    for x = ROOT[1], fx1, 0.2 do
      local u = math.min(1, (x - ROOT[1]) / 1.5)
      u = u * u * (3 - 2 * u)
      foot[#foot + 1] = { x, ROOT[2] + 0.1 + (0.95 - ROOT[2] - 0.1 + 0.2 * f(x / 3.5)) * u }
    end
    F.stem(foot, 0.065, 0.01)
  end

  -- terminal flowers
  for _, name in ipairs({ "A", "B", "C" }) do
    local st = STEMS[name]
    local pts = stems[name]
    local p, q = pts[#pts], pts[#pts - 3]
    local ax, ay = norm(p[1] - q[1], p[2] - q[2])
    local kind, s, a = st.tip[1], st.tip[2], st.tip[3]
    local m = grow.motifs[kind]
    local r = rng.fork()
    place(m.layer, p[1] + ax * 0.2, p[2] + ay * 0.2, a, function() m.draw(r, s) end)
  end

  -- ghosts behind everything
  for _, gh in ipairs(GHOSTS) do
    local r = rng.fork()
    place(LY.ghost, gh[1], gh[2], 90, function() F.ghost(0.62, function() F.flower(r, gh[3]) end) end)
  end

  -- leaves at the nodes
  for _, lf in ipairs(LEAVES) do
    local x, y, tx, ty = at(stems[lf[1]], lf[2])
    local a = deg(tx, ty) + lf[3] * jit.range(40, 55)
    local L = lf[4] * 1.12 * jit.range(0.92, 1.05)
    local r = rng.fork()
    local bend = lf[3] * jit.range(0.08, 0.3)
    place(LY.leaf, x, y, a, function()
      ink.scale(L) F.leaf(r, { w = 0.26, depth = lf[5] and jit.range(0.45, 0.75) or 0, bend = bend })
    end)
  end
  -- leaflets along the footer, smaller toward its end
  do
    local s, tot = ink.arclen(foot)
    local side, nexts = 1, 0.7
    for i = 2, #foot - 2 do
      if s[i] >= nexts then
        local u = s[i] / tot
        nexts = nexts + (0.55 + 0.8 * u) * jit.range(0.85, 1.15)
        side = -side
        local tx, ty = norm(foot[i + 1][1] - foot[i - 1][1], foot[i + 1][2] - foot[i - 1][2])
        local L = (0.9 - 0.45 * u) * jit.range(0.85, 1.1)
        local a = deg(tx, ty) + side * jit.range(35, 55)
        local r = rng.fork()
        local bend = -side * 0.2
        place(LY.leaf, foot[i][1], foot[i][2], a, function() ink.scale(L) F.leaflet(r, { bend = bend }) end)
      end
    end
  end

  -- branches and their motifs
  local function grow_branch(sx, sy, tx, ty, px, py, kind, s, w0)
    local m = grow.motifs[kind]
    local dx, dy = norm(px - sx, py - sy)
    local ax, ay = norm(dx, dy + (m.upright or 0))
    local ox, oy = px - ax * m.off(s), py - ay * m.off(s)
    if m.hang then ox, oy = px - dx * 0.2 * s, py + 0.45 * s end
    local bpts = F.branch_path(jit, sx, sy, tx, ty, ox, oy, m.hang and dx or ax, m.hang and -0.3 or ay)
    ink.layer(LY.stem)
    F.stem(bpts, w0, 0.014)
    local d = sqrt((ox - sx) ^ 2 + (oy - sy) ^ 2)
    if d > 1.0 then
      local i = floor(#bpts * 0.4)
      local p, q = bpts[i], bpts[i + 1]
      local a = deg(q[1] - p[1], q[2] - p[2]) + (jit.chance(0.5) and 1 or -1) * jit.range(40, 60)
      local ls = jit.range(0.45, 0.7)
      local r = rng.fork()
      place(LY.leaf, p[1], p[2], a, function() ink.scale(ls) F.leaflet(r) end)
    end
    local r = rng.fork()
    place(m.layer, ox, oy, m.hang and 90 or deg(ax, ay), function() m.draw(r, s) end)
  end
  for _, b in ipairs(BRANCHES) do
    local x, y, tx, ty = at(stems[b[1]], b[2])
    grow_branch(x, y, tx, ty, b[3] + jit.sym(0.1), b[4] + jit.sym(0.1), b[5], b[6], 0.035)
  end
  for _, b in ipairs(FOOT) do
    if b[1] < fx1 - 0.5 then
      local best, bi = math.huge, 1
      for i, p in ipairs(foot) do local d = math.abs(p[1] - (b[1] - 0.4)) if d < best then best, bi = d, i end end
      local p, q = foot[bi], foot[min(#foot, bi + 1)]
      local tx, ty = norm(q[1] - p[1], q[2] - p[2])
      grow_branch(p[1], p[2], tx, ty, b[1], p[2] + 0.45, b[2], b[3], 0.025)
    end
  end

  -- accents and the footer's copper tail
  for _, ac in ipairs(ACCENTS) do
    local r = rng.fork()
    place(LY.accent, ac[2], ac[3], 90, function() F[ac[1]](r, ac[1] == "sparkle" and 0.13 or 0.12) end)
  end
  do
    local e = foot[#foot]
    local x2 = e[1] + 1.9
    ink.layer(LY.accent)
    ink.moveto(e[1], e[2]) ink.curveto(e[1] + 0.6, e[2] + 0.05, x2 - 0.6, e[2] - 0.05, x2, e[2])
    ink.stroke(ink.accent(0), 0.3, 0.8)
    place(LY.accent, x2 + 0.18, e[2], 90, function() F.sparkle(rng.fork(), 0.12, { rays = false }) end)
    ink.circle(x2 + 0.45, e[2], 0.025) ink.fill(ink.accent(0))
  end

  -- visitors last, from their own stream, so the rest of the page does not change
  if g.visitors ~= false then
    local vr = ink.rng(g.seed * 7919 + 103)
    for _, v in ipairs(VISITORS) do
      local r = vr.fork()
      place(LY.accent, v[2], v[3], v[5], function() F[v[1]](r, v[4]) end)
    end
    local x, y, tx, ty = at(stems[SNAIL[1]], SNAIL[2])
    local r = vr.fork()
    place(LY.accent, x + ty * SNAIL[3] * 0.03, y - tx * SNAIL[3] * 0.03, deg(tx, ty), function()
      ink.scale(SNAIL[3], 1) F.snail(r, SNAIL[4]) end)
  end

  -- a safety clip: the column (a little past its edge) and the footer band
  ink.layer(0)
  ink.poly({ { 0, 0 }, { g.colright + 0.25, 0 }, { g.colright + 0.25, g.ph }, { 0, g.ph } }, true)
  ink.poly({ { g.colright, 0 }, { fx1 + 3, 0 }, { fx1 + 3, min(2.0, g.footy - 0.2) }, { g.colright, min(2.0, g.footy - 0.2) } }, true)
  ink.clip()
  ink.layer(99)
  ink.unclip()
  ink.flush()
end

return M
