-- theme-geometric.lua -- a theme for florilegium: the same plant, cut from flat
-- shapes with straight edges.
-- Copyright (c) 2026 Kevin Raymond. MIT License: see LICENSE or florilegium.sty.
--
-- grow.lua draws every primitive through the current theme, so the garden grows
-- exactly as it does with flora: the stems sway up the column, leaves hang at the
-- nodes, the loop fills the holes. Only the drawing changes. Stems run straight
-- between nodes a centimeter or so apart; leaves are kites or toothed polygons,
-- folded into a light and a dark facet with straight white veins; flowers are
-- rosettes of rhombi or layered star polygons; buds, bells, sprays, umbels, the
-- tendril (a square spiral) and the visitors are polygons too. Colors are flat
-- tones of the ink, with no wash, mottle or streak; copper marks the centers.
-- One motif is added: crystals (Platonic solids, flat-shaded like cut stones).
-- Use: \usepackage[grown,theme=geometric]{florilegium}.

local ink = require("ink")
local flora = require("flora")
local figures = require("figures")
local M = {}

local sin, cos, sqrt, pi, abs, floor, max, min = math.sin, math.cos, math.sqrt, math.pi, math.abs, math.floor, math.max, math.min
local tone, white = ink.tone, ink.white
local rad = pi / 180
local PHI = (1 + sqrt(5)) / 2
local function lerp(a, b, t) return a + (b - a) * t end
local function ghost() return ink.get_lift() > 0.3 end
local function fine(u) return ink.unit() > (u or 0.25) and not ghost() end

-- a flat facet; white seams between facets; points turned by a (radians)
local function facet(pts, c, op) ink.poly(pts, true) ink.fill(c, op) end
local function turn(pts, a)
  local c, s, out = cos(a), sin(a), {}
  for i, p in ipairs(pts) do out[i] = { p[1] * c - p[2] * s, p[1] * s + p[2] * c } end
  return out
end
local function ngon(n, r, a0, cx, cy)
  local out = {}
  for k = 0, n - 1 do local a = (a0 or 0) + 2 * pi * k / n out[#out + 1] = { (cx or 0) + r * cos(a), (cy or 0) + r * sin(a) } end
  return out
end

-- ---------------------------------------------------------------- stems
-- straight runs between points about a quarter of the stem apart (at most 1.2 cm,
-- at least 0.3), as a ribbon with mitered corners; thin ones as a stroke
function M.stem(pts, w0, w1, c, op, tip)
  local s, L = ink.arclen(pts)
  local seg = max(0.3, min(1.2, L / 4))
  local keep, ks, nextat = { pts[1] }, { 0 }, seg
  for i = 2, #pts - 1 do
    if s[i] >= nextat then keep[#keep + 1] = pts[i] ks[#ks + 1] = s[i] nextat = s[i] + seg end
  end
  keep[#keep + 1] = pts[#pts] ks[#ks + 1] = L
  local wbp = (w0 + w1) / 2 * ink.unit() * ink.CM
  if wbp < 0.7 or #keep < 2 then
    ink.poly(keep, false) ink.stroke(c or tone(0.07), max(0.15, wbp), op)
    return
  end
  local f = tip and min(1, tip / max(L, 1e-9)) or 0
  local function width(t) return lerp(w0, w1, t) * ((tip and t > 1 - f) and lerp(1, 0.15, (t - 1 + f) / f) or 1) end
  local function nrm(a, b)
    local dx, dy = b[1] - a[1], b[2] - a[2]
    local l = sqrt(dx * dx + dy * dy)
    if l < 1e-9 then return 0, 1 end
    return -dy / l, dx / l
  end
  local left, right = {}, {}
  for i = 1, #keep do
    local ax, ay, bx, by
    if i > 1 then ax, ay = nrm(keep[i - 1], keep[i]) end
    if i < #keep then bx, by = nrm(keep[i], keep[i + 1]) end
    ax, ay = ax or bx, ay or by
    bx, by = bx or ax, by or ay
    local nx, ny = ax + bx, ay + by
    local l = sqrt(nx * nx + ny * ny)
    if l < 1e-9 then nx, ny = ax, ay else nx, ny = nx / l, ny / l end
    local h = width(ks[i] / L) / 2 / max(0.5, nx * ax + ny * ay)
    left[i] = { keep[i][1] + nx * h, keep[i][2] + ny * h }
    right[i] = { keep[i][1] - nx * h, keep[i][2] - ny * h }
  end
  for i = #right, 1, -1 do left[#left + 1] = right[i] end
  facet(left, c or tone(0.07), op)
end

-- ---------------------------------------------------------------- foliage
-- A leaf pointing +y, length 1: a kite, or with depth > 0 a polygon with
-- triangular lobes, folded along a straight midrib into a light and a dark half,
-- with straight white veins. Opts as flora.leaf: w, depth, lobes, bend, tone.
function M.leaf(rng, o)
  o = o or {}
  local W = o.w or rng.range(0.2, 0.27)
  local bend = 0.5 * (o.bend or rng.sym(0.25))
  local depth = o.depth or rng.range(0.3, 0.7)
  local t0 = o.tone or rng.range(0.26, 0.38)
  local lobes = depth > 0 and (o.lobes or rng.int(2, 4)) or 0
  local function half(v) return W * 2.5 * v ^ 0.6 * (1 - v) end
  local function side(sg)
    local pts, tips = {}, {}
    if lobes == 0 then
      pts[1] = { bend * 0.38 + sg * half(0.38) * 1.15, 0.38 }
      tips[1] = { pts[1], 0.3 }
    else
      for k = 1, lobes do
        local v1, v2 = 0.1 + 0.78 * (k - 0.35) / lobes, 0.1 + 0.78 * k / lobes
        local p = { bend * v1 + sg * half(v1) * 1.2, v1 + 0.07 }
        pts[#pts + 1] = p
        pts[#pts + 1] = { bend * v2 + sg * half(v2) * (1 - 0.7 * depth), v2 }
        tips[#tips + 1] = { p, v1 - 0.06 }
      end
    end
    return pts, tips
  end
  local tip = { bend, 1 }
  local function halfpoly(pts, sg)
    local out = { { 0, 0 } }
    for _, p in ipairs(pts) do out[#out + 1] = p end
    out[#out + 1] = tip
    return out
  end
  local Lp, Lt = side(-1)
  local Rp, Rt = side(1)
  local dark = rng.chance(0.5) and 1 or -1
  facet(halfpoly(Lp), tone(t0 + 0.1 * dark))
  facet(halfpoly(Rp), tone(t0 - 0.1 * dark))
  if fine() then
    ink.moveto(0, 0) ink.lineto(tip[1], tip[2])
    for _, tp in ipairs({ Lt, Rt }) do
      for _, t in ipairs(tp) do
        local p, v = t[1], t[2]
        ink.moveto(bend * v, v) ink.lineto(lerp(bend * v, p[1], 0.85), lerp(v, p[2], 0.85))
      end
    end
    if lobes == 0 then                                   -- two more veins a side on a kite
      for _, v in ipairs({ 0.55, 0.72 }) do
        for _, sg in ipairs({ -1, 1 }) do
          local w = half(0.38) * 1.15 * (1 - v) / 0.62
          ink.moveto(bend * v, v) ink.lineto(bend * (v + 0.1) + sg * w * 0.8, v + 0.1)
        end
      end
    end
    ink.stroke(white, 0.35, 0.85)
  end
end

-- a small leaf: a kite in two facets
function M.leaflet(rng, o)
  o = o or {}
  local W = o.w or rng.range(0.16, 0.24)
  local bend = 0.5 * (o.bend or rng.sym(0.2))
  local t0 = o.tone or rng.range(0.2, 0.34)
  local tip, l, r = { bend, 1 }, { bend * 0.4 - W, 0.4 }, { bend * 0.4 + W, 0.4 }
  local dark = rng.chance(0.5) and 1 or -1
  facet({ { 0, 0 }, l, tip }, tone(t0 + 0.08 * dark))
  facet({ { 0, 0 }, r, tip }, tone(t0 - 0.08 * dark))
  if fine(0.3) then ink.moveto(0, 0) ink.lineto(tip[1], tip[2]) ink.stroke(white, 0.3, 0.8) end
end

-- a petal (falling, or loose): a rhombus in two facets, length 1
function M.petal(rng, o)
  o = o or {}
  local W = o.w or rng.range(0.22, 0.3)
  local t0 = o.tone or rng.range(0.34, 0.42)
  facet({ { 0, 0 }, { W, 0.5 }, { 0, 1 } }, tone(t0 - 0.06))
  facet({ { 0, 0 }, { 0, 1 }, { -W, 0.5 } }, tone(t0 + 0.06))
end

-- ---------------------------------------------------------------- flowers
-- the center: a pale polygon, its navy rim, a copper point
local function center(n, r, a0)
  facet(ngon(n, r, a0), white, 0.92)
  ink.poly(ngon(n, r, a0), true) ink.stroke(tone(0.06), 0.4, 0.85)
  ink.circle(0, 0, r * 0.3) ink.fill(ink.accent(-0.1))
end

-- A flower seen from the front, radius s (cm): five, six or eight rhombus petals,
-- each split along its axis into a light and a dark facet, darker triangles
-- between them; or a star polygon over a smaller one turned half a step.
function M.flower(rng, s, o)
  o = o or {}
  ink.push() ink.scale(s) ink.rotate(rng.range(0, 360))
  local n = o.petals or ({ 5, 6, 8 })[rng.int(1, 3)]
  local t0 = o.tone or (rng.chance(0.25) and rng.range(0.18, 0.26) or rng.range(0.3, 0.42))
  if (o.style or rng.int(1, 2)) == 1 then
    local w = 0.55 * sin(pi / n) * 0.95                  -- the petals just meet at their widest
    for k = 0, n - 1 do                                   -- darker facets between them, behind
      facet(turn({ { 0, 0.1 }, { w * 0.5, 0.45 }, { 0, 0.7 }, { -w * 0.5, 0.45 } }, 2 * pi * k / n + pi / n), tone(t0 - 0.16))
    end
    for k = 0, n - 1 do
      local P = turn({ { 0, 0.12 }, { w, 0.55 }, { 0, 1 }, { -w, 0.55 } }, 2 * pi * k / n)
      facet({ P[1], P[2], P[3] }, tone(t0 - 0.07))
      facet({ P[1], P[3], P[4] }, tone(t0 + 0.09))
    end
  else
    for layer = 1, 2 do
      local R, r, a0 = layer == 1 and 1 or 0.66, layer == 1 and 0.42 or 0.3, layer == 1 and 0 or pi / n
      for k = 0, n - 1 do
        local a = a0 + 2 * pi * k / n
        local O = { R * cos(a + pi / 2), R * sin(a + pi / 2) }
        local L = { r * cos(a + pi / 2 - pi / n), r * sin(a + pi / 2 - pi / n) }
        local Rr = { r * cos(a + pi / 2 + pi / n), r * sin(a + pi / 2 + pi / n) }
        local t = layer == 1 and t0 or t0 + 0.22
        facet({ { 0, 0 }, L, O }, tone(t - 0.07))
        facet({ { 0, 0 }, O, Rr }, tone(t + 0.07))
      end
    end
  end
  center(n, 0.17, pi / 2)
  ink.pop()
end

-- A star lily seen at a tilt: six triangular petals squashed along y, those behind
-- darker; straight stamens. Center at the origin, faces +y; s = petal length.
function M.lily(rng, s, o)
  o = o or {}
  ink.push() ink.scale(s)
  local tilt = o.tilt or rng.range(0.45, 0.62)
  local t0 = o.tone or rng.range(0.3, 0.38)
  local spin = rng.range(0, 60)
  local order = {}
  for k = 0, 5 do order[#order + 1] = spin + k * 60 end
  table.sort(order, function(a, b) return sin(a * rad) > sin(b * rad) end)
  for _, a in ipairs(order) do
    local back = sin(a * rad)
    local P = turn({ { 0, 0 }, { 0.14, 0.38 }, { 0, 1 }, { -0.14, 0.38 } }, (a - 90) * rad)
    for i, p in ipairs(P) do P[i] = { p[1], p[2] * tilt } end
    local t = t0 - 0.08 * back
    facet({ P[1], P[2], P[3] }, tone(t - 0.06))
    facet({ P[1], P[3], P[4] }, tone(t + 0.08))
  end
  if fine(0.3) then
    for k = 1, 5 do
      local a = (k - 3) * 15 * rad
      local x, y = 0.42 * sin(a), 0.42 * cos(a)
      ink.moveto(0, 0) ink.lineto(x, y)
    end
    ink.stroke(tone(0.1), 0.3, 0.85)
    for k = 1, 5 do
      local a = (k - 3) * 15 * rad
      local x, y = 0.42 * sin(a), 0.42 * cos(a)
      ink.poly({ { x, y - 0.03 }, { x + 0.02, y }, { x, y + 0.03 }, { x - 0.02, y } }, true)
    end
    ink.fill(tone(0.05))
  end
  ink.circle(0, 0, 0.035) ink.fill(ink.accent(-0.2))
  ink.pop()
end

-- a small flower: five kites, a pale center, a navy eye. r = radius (cm)
function M.blossom(rng, r, o)
  o = o or {}
  ink.push() ink.scale(r) ink.rotate(rng.range(0, 72))
  local t0 = o.tone or rng.range(0.3, 0.45)
  for k = 0, 4 do
    local P = turn({ { 0, 0.1 }, { 0.34, 0.6 }, { 0, 1 }, { -0.34, 0.6 } }, k * 2 * pi / 5)
    facet({ P[1], P[2], P[3] }, tone(t0 - 0.06))
    facet({ P[1], P[3], P[4] }, tone(t0 + 0.06))
  end
  facet(ngon(5, 0.24, pi / 2), white, 0.9)
  facet(ngon(5, 0.1, pi / 2), o.eye or tone(0.08))
  ink.pop()
end

-- a floret a few millimeters across: a five-pointed star, a dark eye
function M.floret(rng, r, o)
  o = o or {}
  local ph, pts = rng.range(0, 2 * pi), {}
  for k = 0, 9 do
    local a = ph + k * pi / 5
    local d = (k % 2 == 0) and r or r * 0.42
    pts[#pts + 1] = { d * cos(a), d * sin(a) }
  end
  facet(pts, tone(o.tone or rng.range(0.22, 0.42)))
  facet(ngon(5, 0.2 * r, ph), o.eye or tone(0.05))
end

-- a closed bud: a long rhombus in two facets, three triangular sepals. +y, length s
function M.bud(rng, s, o)
  o = o or {}
  ink.push() ink.scale(s)
  local bend = rng.sym(0.08)
  local t0 = o.tone or rng.range(0.3, 0.42)
  facet({ { 0, 0 }, { 0.24, 0.42 }, { bend, 1 } }, tone(t0 - 0.07))
  facet({ { 0, 0 }, { bend, 1 }, { -0.24, 0.42 } }, tone(t0 + 0.08))
  for k = -1, 1 do
    facet(turn({ { -0.05, -0.02 }, { 0.05, -0.02 }, { 0, k == 0 and 0.24 or 0.3 } }, -k * 28 * rad), tone(0.12))
  end
  ink.pop()
end

-- a bellflower hanging from the origin along -y: a flared trapezoid with a
-- zigzag rim, in three facets, a calyx of triangles. s = length
function M.bell(rng, s, o)
  o = o or {}
  ink.push() ink.scale(s) ink.rotate(rng.sym(8))
  local t0 = o.tone or rng.range(0.3, 0.4)
  local rim = { { 0.45, -0.98 }, { 0.3, -0.86 }, { 0.15, -1.0 }, { 0, -0.88 }, { -0.15, -1.0 }, { -0.3, -0.86 }, { -0.45, -0.98 } }
  local body = { { 0.12, -0.02 } }
  for _, p in ipairs(rim) do body[#body + 1] = p end
  body[#body + 1] = { -0.12, -0.02 }
  facet(body, tone(t0))
  facet({ { 0.12, -0.02 }, { 0.45, -0.98 }, { 0.3, -0.86 }, { 0.15, -1.0 }, { 0.06, -0.02 } }, tone(t0 - 0.1))
  facet({ { -0.12, -0.02 }, { -0.06, -0.02 }, { -0.15, -1.0 }, { -0.3, -0.86 }, { -0.45, -0.98 } }, tone(t0 + 0.12))
  for k = -1, 1 do
    facet(turn({ { -0.05, 0.02 }, { 0.05, 0.02 }, { 0, 0.28 } }, (180 + k * 40) * rad), tone(0.1))
  end
  ink.pop()
end

-- ---------------------------------------------------------------- sprays
-- a forget-me-not cyme: a stalk that turns more at each step, straight between
-- them, florets crowding along it and shrinking into buds. Starts heading +y.
local function curl(rng, x, y, h0, L, side, t0, w)
  local N, turnall = 9, rng.range(170, 260)
  local pts, a = { { x, y } }, h0
  for i = 1, N do
    a = a + side * turnall * ((i / N) ^ 2.3 - ((i - 1) / N) ^ 2.3)
    x, y = x + L / N * cos(a * rad), y + L / N * sin(a * rad)
    pts[#pts + 1] = { x, y }
  end
  ink.poly(pts, false) ink.stroke(tone(0.1), max(0.2, w * ink.unit() * ink.CM))
  for i = 2, #pts do
    local f = (i - 1) / N
    local p, q = pts[i - 1], pts[i]
    local dx, dy = q[1] - p[1], q[2] - p[2]
    local l = sqrt(dx * dx + dy * dy)
    local sg = i % 2 == 0 and 1 or -1
    local r = lerp(0.11, 0.035, f)
    local cx, cy = q[1] - dy / l * sg * (r + 0.02), q[2] + dx / l * sg * (r + 0.02)
    ink.push() ink.translate(cx, cy)
    if f > 0.75 then facet(ngon(4, r * 0.7, rng.range(0, pi)), tone(t0 - 0.06))
    else facet(ngon(5, r, rng.range(0, 2 * pi)), tone(t0 + rng.sym(0.08))) facet(ngon(5, r * 0.3, 0), tone(0.05)) end
    ink.pop()
  end
  return pts
end
function M.cyme(rng, L, o)
  o = o or {}
  local side = o.side or (rng.chance(0.5) and 1 or -1)
  local t0 = rng.range(0.22, 0.36)
  local pts = curl(rng, 0, 0, 90 + rng.sym(10), L, side, t0, 0.024)
  if (o.fork ~= false) and rng.chance(o.fork and 1 or 0.6) then
    local i = rng.int(3, 4)
    local a = math.atan(pts[i + 1][2] - pts[i][2], pts[i + 1][1] - pts[i][1]) / rad
    curl(rng, pts[i][1], pts[i][2], a - side * rng.range(30, 50), L * rng.range(0.45, 0.65), -side, t0 + 0.04, 0.016)
  end
end

-- a branching sprig, straight between the forks; star florets and diamond buds
-- at the tips, kites at the lower forks. Starts heading +y, length L.
function M.sprig(rng, L, o)
  o = o or {}
  local depth = o.depth or 4
  local t0 = rng.range(0.22, 0.4)
  local function branch(x, y, a, len, d, w)
    local ex, ey = x + len * cos(a * rad), y + len * sin(a * rad)
    ink.moveto(x, y) ink.lineto(ex, ey) ink.stroke(tone(0.1), max(0.2, w * ink.unit() * ink.CM))
    if d == 0 then
      ink.push() ink.translate(ex, ey)
      if rng.chance(0.7) then M.floret(rng, rng.range(0.045, 0.075), { tone = t0 + rng.sym(0.08) })
      else facet(ngon(4, rng.range(0.02, 0.03), a * rad), tone(t0 - 0.05)) end
      ink.pop()
      return
    end
    if d >= depth - 1 and rng.chance(0.7) then
      local sg = rng.chance(0.5) and 1 or -1
      ink.push() ink.translate(ex, ey) ink.rotate(a - 90 + sg * rng.range(40, 70)) ink.scale(len * rng.range(0.5, 0.8))
      M.leaflet(rng, { w = 0.14 })
      ink.pop()
    end
    local kids = rng.chance(0.25) and 3 or 2
    for k = 1, kids do
      local da = (kids == 2) and (k == 1 and -1 or 1) * rng.range(18, 34) or (k - 2) * rng.range(24, 36)
      branch(ex, ey, a + da, len * rng.range(0.58, 0.74), d - 1, w * 0.72)
    end
  end
  branch(0, 0, 90 + rng.sym(8), L * 0.36, depth, 0.024)
end

-- an umbel: straight rays fanning upward, each ending in a little umbel of star
-- florets; triangular bracts at the base. R = reach (cm)
function M.umbel(rng, R, o)
  local nr = rng.int(9, 13)
  for k = 1, nr do
    local a = (90 + (k - (nr + 1) / 2) * (110 / nr) + rng.sym(4)) * rad
    local L = R * rng.range(0.78, 1.0) * (1 - 0.15 * abs(a / rad - 90) / 55)
    local ex, ey = L * cos(a), L * sin(a)
    ink.moveto(0, 0) ink.lineto(ex, ey) ink.stroke(tone(0.12), 0.25, 0.9)
    local ns = rng.int(5, 7)
    for j = 1, ns do
      local b = a + ((j - (ns + 1) / 2) * 16 + rng.sym(5)) * rad
      local l = R * rng.range(0.12, 0.2)
      ink.moveto(ex, ey) ink.lineto(ex + l * cos(b), ey + l * sin(b)) ink.stroke(tone(0.14), 0.18, 0.85)
      ink.push() ink.translate(ex + l * cos(b), ey + l * sin(b))
      M.floret(rng, R * rng.range(0.035, 0.05), { tone = rng.range(0.25, 0.42) })
      ink.pop()
    end
  end
  for k = -1, 1 do
    facet(turn({ { -0.03 * R, 0 }, { 0.03 * R, 0 }, { 0, -0.2 * R } }, k * 40 * rad), tone(0.15))
  end
end

-- a square spiral: straight runs, each turning left a right angle and shorter by
-- the golden ratio. Starts at the origin; s = size (cm)
function M.tendril(rng, s)
  local pts, x, y, a, l = { { 0, 0 } }, 0, 0, 90, s * 1.15
  for _ = 1, 9 do
    x, y = x + l * cos(a * rad), y + l * sin(a * rad)
    pts[#pts + 1] = { x, y }
    a, l = a + 90, l / PHI
  end
  ink.poly(pts, false) ink.stroke(tone(0.12), 0.45)
end

-- a rosette accent: the star polygon {8/3} in a copper hairline
function M.rosette(rng, r, o)
  local c = (o and o.color) or ink.accent(0)
  local pts = {}
  for k = 0, 7 do local a = (k * 3 * 45 + 22.5) * rad pts[#pts + 1] = { 1.3 * r * cos(a), 1.3 * r * sin(a) } end
  ink.poly(pts, true) ink.stroke(c, 0.22, 0.85)
  ink.circle(0, 0, r * 0.14) ink.fill(c)
end

-- the header fleuron: a copper kite leaf, tip down-left, its stem straight out
-- to the right where the head rule continues. Returns the stem's end in page cm.
function M.hedera(rng, s, o)
  local c = (o and o.color) or ink.accent(0)
  ink.push() ink.scale(s)
  local P = turn({ { 0, 0 }, { 0.42, -0.45 }, { 0, -1.25 }, { -0.42, -0.45 } }, -38 * rad)
  facet(P, c)
  ink.moveto(P[1][1], P[1][2]) ink.lineto(P[3][1], P[3][2]) ink.stroke(ink.paper, 0.35)
  ink.poly({ { 0, 0 }, { 0.3, 0.36 }, { 0.9, 0.36 }, { 2.0, 0.28 } }, false) ink.stroke(c, 0.4)
  local rx, ry = ink.to_page(2.0, 0.28)
  ink.pop()
  return rx, ry
end

-- ---------------------------------------------------------------- visitors
-- a fan of facets from `root` to the outline's consecutive corners, tones alternating
local function fan(root, pts, t0, dt)
  for i = 1, #pts - 1 do facet({ root, pts[i], pts[i + 1] }, tone(t0 + (i % 2 == 0 and dt or -dt))) end
end

-- a butterfly from above, wings of straight-edged facets; s = wingspan, o.open
-- narrows the wings (a wingbeat). Head toward +y, center at the origin.
function M.butterfly(rng, s, o)
  o = o or {}
  local open = o.open or 1
  ink.push() ink.scale(s / 2)
  local t0 = o.tone or rng.range(0.28, 0.4)
  local FW = { { 0.05, 0.1 }, { 0.3, 0.48 }, { 0.68, 0.7 }, { 0.98, 0.62 }, { 0.9, 0.3 }, { 0.55, 0.06 }, { 0.12, -0.02 } }
  local HW = { { 0.06, -0.02 }, { 0.5, -0.04 }, { 0.74, -0.3 }, { 0.6, -0.68 }, { 0.3, -0.7 }, { 0.08, -0.36 } }
  for _, sx in ipairs({ -1, 1 }) do
    local function side(w) local out = {} for i, p in ipairs(w) do out[i] = { sx * p[1] * open, p[2] } end return out end
    fan({ sx * 0.03 * open, -0.03 }, side(HW), t0 + 0.08, 0.06)
    fan({ sx * 0.03 * open, 0.04 }, side(FW), t0, 0.07)
    if fine(0.3) then
      facet({ { sx * 0.62 * open, 0.42 }, { sx * 0.7 * open, 0.48 }, { sx * 0.62 * open, 0.54 }, { sx * 0.54 * open, 0.48 } }, ink.accent(0))
    end
  end
  facet({ { 0, 0.3 }, { 0.05, 0.12 }, { 0.04, -0.3 }, { 0, -0.6 }, { -0.04, -0.3 }, { -0.05, 0.12 } }, tone(0.05))
  ink.poly({ { -0.22, 0.86 }, { -0.03, 0.32 }, { 0.03, 0.32 }, { 0.22, 0.86 } }, false) ink.stroke(tone(0.08), 0.35)
  ink.pop()
end

-- a bee from above: a faceted hexagonal abdomen with bands, a dark thorax, pale
-- rhombic wings. Head toward +y; s = body length
function M.bee(rng, s, o)
  ink.push() ink.scale(s)
  local ab = { { 0, 0.08 }, { 0.17, -0.02 }, { 0.17, -0.34 }, { 0, -0.52 }, { -0.17, -0.34 }, { -0.17, -0.02 } }
  facet(ab, tone(0.4))
  for k = 0, 2 do
    local y = -0.08 - 0.13 * k
    facet({ { -0.17, y + 0.03 }, { 0.17, y + 0.03 }, { 0.17, y - 0.03 }, { -0.17, y - 0.03 } }, tone(0.05))
  end
  facet(ngon(6, 0.13, pi / 6, 0, 0.16), tone(0.06))
  facet(ngon(5, 0.08, pi / 2, 0, 0.34), tone(0.04))
  for _, sx in ipairs({ -1, 1 }) do
    local W = { { sx * 0.06, 0.18 }, { sx * 0.3, 0.32 }, { sx * 0.5, 0.2 }, { sx * 0.26, 0.06 } }
    facet(W, tone(0.86), 0.6)
    ink.poly(W, true) ink.stroke(tone(0.2), 0.3, 0.8)
  end
  ink.pop()
end

-- a snail crawling up +y, foot on the y axis, shell on the +x side: the shell a
-- golden rectangle cut into squares, a straight-edged spiral through them.
-- s = shell diameter
function M.snail(rng, s, o)
  ink.push() ink.scale(s)
  facet({ { 0, -0.78 }, { 0.12, -0.45 }, { 0.17, 0.3 }, { 0.24, 0.5 }, { 0.22, 0.66 }, { 0.12, 0.7 }, { 0.04, 0.58 }, { -0.01, -0.3 } }, tone(0.55))
  ink.poly({ { 0.17, 0.66 }, { 0.36, 1.02 } }, false) ink.poly({ { 0.1, 0.7 }, { 0.18, 1.04 } }, false) ink.stroke(tone(0.12), 0.4)
  -- the golden rectangle, standing, its squares spiraling in
  local x, y, w, h = 0.36 - 0.27, -0.42, 0.52, 0.84
  local spiral = {}
  for i = 0, 7 do
    local d, sq = i % 4, nil
    if d == 0 then sq = { x, y + h - w, w } spiral[#spiral + 1] = { x, y + h } h = h - w
    elseif d == 1 then sq = { x + w - h, y, h } spiral[#spiral + 1] = { x + w, y + h } w = w - h
    elseif d == 2 then sq = { x, y, w } spiral[#spiral + 1] = { x + w, y } y, h = y + w, h - w
    else sq = { x, y, h } spiral[#spiral + 1] = { x, y } x, w = x + h, w - h end
    facet({ { sq[1], sq[2] }, { sq[1] + sq[3], sq[2] }, { sq[1] + sq[3], sq[2] + sq[3] }, { sq[1], sq[2] + sq[3] } },
      tone(0.22 + 0.08 * (i % 3)))
  end
  ink.poly(spiral, false) ink.stroke(white, 0.35, 0.85)
  ink.pop()
end

-- a perched bird facing +x (o.facing = -1: -x), feet at the origin, all facets:
-- a fan from the middle of the body, the breast lighter; s = tail to beak
function M.bird(rng, s, o)
  o = o or {}
  ink.push() ink.scale((o.facing or 1) * s, s)
  local t0 = o.tone or rng.range(0.3, 0.38)
  for k = 1, 3 do
    facet({ { -0.24, 0.3 }, { -0.62 + 0.04 * k, 0.04 - 0.05 * k }, { -0.56 + 0.04 * k, 0.0 - 0.05 * k } }, tone(0.12 + 0.06 * k))
  end
  local body = { { 0.37, 0.56 }, { 0.28, 0.67 }, { 0.12, 0.64 }, { -0.08, 0.52 }, { -0.3, 0.32 }, { -0.24, 0.2 }, { 0.04, 0.12 }, { 0.24, 0.24 }, { 0.36, 0.42 }, { 0.37, 0.56 } }
  for i = 1, #body - 1 do
    local front = body[i][1] > 0.15 and body[i][2] < 0.5
    facet({ { 0.08, 0.4 }, body[i], body[i + 1] }, tone(front and 0.72 or t0 + (i % 2 == 0 and 0.05 or -0.05)))
  end
  facet({ { 0.16, 0.46 }, { -0.12, 0.46 }, { -0.44, 0.22 }, { -0.1, 0.28 } }, tone(t0 - 0.12))
  facet({ { 0.36, 0.585 }, { 0.47, 0.545 }, { 0.36, 0.51 } }, tone(0.05))
  ink.circle(0.285, 0.585, 0.025) ink.fill(tone(0.03))
  ink.poly({ { 0.02, 0.14 }, { 0, 0 } }, false) ink.poly({ { 0.1, 0.14 }, { 0.08, 0 } }, false) ink.stroke(tone(0.06), 0.45)
  ink.pop()
end

-- ---------------------------------------------------------------- new motifs
-- a crystal: a Platonic solid flat-shaded like a cut stone, white edges; r = radius
local crystals = {}
function M.crystal(rng, r, o)
  local i = (o and o.k) or rng.int(1, 5)
  if not crystals[i] then crystals[i] = figures.hull_of(figures.solids[i][3]) end
  local v, h = figures.solids[i][3], crystals[i]
  local rot = figures.rotation(rng.range(0, 360), rng.range(15, 35))
  local k, P = r * 0.95 / h.radius, {}
  for j, q in ipairs(v) do local x, y = rot(q[1], q[2], q[3]) P[j] = { x * k, y * k } end
  local t0 = rng.range(0.2, 0.35)
  for _, f in ipairs(h.faces) do
    local nx, ny, nz = rot(f.n[1], f.n[2], f.n[3])
    if nz > 1e-6 then
      local pts = {}
      for _, m in ipairs(f.v) do pts[#pts + 1] = P[m] end
      local lit = max(0, -0.45 * nx + 0.6 * ny + 0.66 * nz)
      facet(pts, tone(lerp(t0, 0.85, lit)))
      ink.poly(pts, true) ink.stroke(white, 0.3, 0.9)
    end
  end
end

-- ---------------------------------------------------------------- the theme
M.flora = {
  stem = M.stem, leaf = M.leaf, leaflet = M.leaflet, petal = M.petal,
  flower = M.flower, lily = M.lily, blossom = M.blossom, floret = M.floret, bud = M.bud, bell = M.bell,
  cyme = M.cyme, sprig = M.sprig, umbel = M.umbel, tendril = M.tendril, seedhead = figures.phyllotaxis,
  rosette = M.rosette, hedera = M.hedera,
  butterfly = M.butterfly, bee = M.bee, snail = M.snail, bird = M.bird,
  crystal = M.crystal,
}

function M.motifs(rows, F)
  local grow = require("grow")
  local L = grow.layers
  local by = {}
  for _, m in ipairs(rows) do by[m.name] = m end
  local tone = ink.tone
  -- the sprays of grow.lua on straight stalks
  local function spray(rng, s, n0, n1, spread, fn)
    local n = rng.int(n0, n1)
    for k = 1, n do
      local a = ((k - (n + 1) / 2) * spread + rng.sym(10)) * rad
      local d = s * rng.range(0.45, 0.8) * (k == 1 and 1 or rng.range(0.85, 1.1))
      local x, y = d * sin(a), d * cos(a)
      ink.moveto(0, 0) ink.lineto(x, y) ink.stroke(tone(0.1), 0.35)
      ink.push() ink.translate(x, y) fn(a) ink.pop()
    end
  end
  by.blossoms.draw = function(rng, s)
    spray(rng, s, 2, 4, 38, function() F.blossom(rng, s * rng.range(0.38, 0.5)) end)
    if rng.chance(0.6) then ink.push() ink.rotate(rng.sym(50)) ink.scale(0.5 * s) F.bud(rng, 1) ink.pop() end
  end
  by.budding.draw = function(rng, s)
    spray(rng, s, 2, 4, 34, function(a) ink.rotate(-a / rad * 0.6) F.bud(rng, s * rng.range(0.45, 0.6)) end)
  end
  by.bells.draw = function(rng, s)
    F.bell(rng, s)
    ink.moveto(0, 0) ink.lineto(0.3 * s, 0.2 * s) ink.lineto(0.5 * s, 0.1 * s) ink.stroke(tone(0.1), 0.35)
    ink.push() ink.translate(0.5 * s, 0.1 * s) F.bell(rng, 0.75 * s) ink.pop()
  end
  rows[#rows + 1] = { name = "crystal", w = 1.2, smin = 0.45, smax = 0.8, max = 2, hard = true, layer = L.bloom, upright = 0.4,
    r = function(s) return 1.0 * s end, off = function(s) return 0 end,
    draw = function(rng, s) F.crystal(rng, s) end }
  return rows
end

return M
