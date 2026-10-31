-- flora.lua -- the primitives of florilegium, drawn with ink.lua.
-- Copyright (c) 2026 Kevin Raymond. MIT License: see LICENSE or florilegium.sty.
--
-- Every primitive draws in its own local frame (centimeters, origin at its base
-- or center, pointing along +y unless noted) under the current ink transform,
-- and takes an rng so that no two instances are alike. Painting is layered like
-- a watercolor: a flat wash, darker blotches multiplied over it, pooling at the
-- edges, pale streaks lifted out, a few fine ink lines on top. There are almost
-- no outlines; edges are defined by the wash.

local ink = require("ink")
local M = {}

local sin, cos, sqrt, pi, abs, floor, max, min = math.sin, math.cos, math.sqrt, math.pi, math.abs, math.floor, math.max, math.min
local tone, white = ink.tone, ink.white
local rad = pi / 180

local function lerp(a, b, t) return a + (b - a) * t end
-- level of detail: how many centimeters one local unit covers on the page,
-- and whether we are drawing a pale ghost (no fine detail then)
local function lod() return ink.unit() end
local function ghost() return ink.get_lift() > 0.3 end

-- ---------------------------------------------------------------- washes
local function speck(x, y, r, a)
  local c, s = cos(a), sin(a)
  ink.poly({ { x + r * c, y + r * s }, { x - 0.6 * r * s, y + 0.6 * r * c }, { x - r * c, y - r * s }, { x + 0.6 * r * s, y - 0.6 * r * c } }, true)
end

-- Granulated watercolor inside the current clip: darker and lighter blotches
-- over a box, then fine specks. `n` blotches of about `size`; `dark`/`light` tones.
local function mottle(rng, x0, y0, x1, y1, n, size, dark, light, specks)
  for _ = 1, n do
    local x, y = rng.range(x0, x1), rng.range(y0, y1)
    local r = size * rng.range(0.5, 1.4)
    ink.smooth(ink.blob(rng, x, y, r, r * rng.range(0.5, 1), 0.35, 7), true)
    if rng.chance(0.6) then ink.fill(tone(dark + rng.sym(0.06)), rng.range(0.10, 0.22), true)
    else ink.fill(tone(light + rng.sym(0.06)), rng.range(0.12, 0.26)) end
  end
  if specks and specks > 0 and not ghost() then
    for _ = 1, specks do speck(rng.range(x0, x1), rng.range(y0, y1), size * rng.range(0.03, 0.08), rng.range(0, pi)) end
    ink.fill(tone(dark - 0.08), rng.range(0.3, 0.5), true)
  end
end
M.mottle = mottle

-- a tapered ribbon along a curve f(v), widths w0 at the start and w1 at the end
local function streak(f, n, w0, w1, c, op, mult)
  local pts = ink.sample(f, n)
  ink.smooth(ink.ribbon(pts, function(u) return lerp(w0, w1, u) * (u < 0.12 and (0.4 + 5 * u) or 1) end), true)
  ink.fill(c, op, mult)
end
M.streak = streak

-- the same along one cubic Bézier (control points), much cheaper
local function streak3(x0, y0, x1, y1, x2, y2, x3, y3, w0, w1, c, op, mult)
  ink.taper(x0, y0, x1, y1, x2, y2, x3, y3, w0, w1)
  ink.fill(c, op, mult)
end
M.streak3 = streak3

-- ---------------------------------------------------------------- petal
-- half-width of an obovate petal: narrow claw, widest at 0.62, elliptical cap
local function round_half(W)
  return function(v)
    local m = 0.62
    if v < m then return W * (0.16 + 0.84 * sin(pi / 2 * v / m) ^ 1.3) end
    local q = (v - m) / (1 - m)
    return W * sqrt(max(0, 1 - q * q))
  end
end

-- Base at the origin, pointing +y, length 1.
--   shape "round":   obovate, narrow claw, elliptical cap, wavy margin, maybe a notch
--   shape "pointed": lanceolate, for lilies and stars
-- Opts: w (half-width), tone (wash), streaks, bend (tip offset), shape, heart (pale base)
function M.petal(rng, o)
  o = o or {}
  local pointed = o.shape == "pointed"
  local W = o.w or (pointed and rng.range(0.15, 0.2) or rng.range(0.40, 0.48))
  local bend = o.bend or rng.sym(0.08)
  local t0 = o.tone or rng.range(0.34, 0.42)
  local u = lod()
  local fine = u > 0.45 and not ghost()
  local wave = ink.fbm1(rng, 3)
  local notch = (not pointed and rng.chance(0.4)) and rng.range(0.03, 0.06) or 0
  local spine = function(v) return bend * v * v, v end
  local half
  if pointed then
    half = function(v) return W * 2 * sin(pi * v ^ 0.8) ^ 0.85 * (1 - 0.3 * v) end
  else
    half = round_half(W)
  end
  local edge = function(v, side)
    local e = (pointed and 0.012 or 0.03) * wave(v * 6 + (side > 0 and 0 or 40)) * v
    if notch > 0 and v > 0.9 then e = e - notch * (v - 0.9) * 10 * (1 - (v - 0.9) * 10) end
    return e
  end
  local outline = ink.blade(spine, u > 0.5 and 28 or 18, half, half, edge)
  ink.smooth(outline, true)
  ink.clip()
    ink.flood(tone(t0), -1, -0.1, 1, 1.2)
    if o.heart ~= false then          -- the heart of the flower is pale
      for k = 1, 8 do
        ink.smooth(ink.blob(rng, 0, 0, W * (0.25 + 0.1 * k), 0.06 + 0.065 * k, 0.28, 9), true)
        ink.fill(white, 0.1)
      end
    end
    mottle(rng, -W * 1.2, 0.12, W * 1.2, 1.05, fine and 15 or 6, pointed and 0.06 or 0.12, t0 - 0.2, t0 + 0.2, fine and 12 or 0)
    -- darker brush strokes running out from the base, between the streaks
    if fine then
      for _ = 1, rng.int(5, 8) do
        local f = rng.sym(0.95)
        local v0, v1 = rng.range(0.15, 0.4), rng.range(0.7, 1.0)
        local x0, x1 = f * half(v0) * 0.8 + bend * v0 * v0, f * half(v1) * 0.9 + bend * v1 * v1
        streak3(x0, v0, x0 + (x1 - x0) * 0.3, lerp(v0, v1, 0.35), x1 * 0.95, lerp(v0, v1, 0.7), x1, v1,
          rng.range(0.03, 0.07), 0.005, tone(t0 - 0.25), rng.range(0.12, 0.25), true)
      end
    end
    -- pooling: the outline restroked wide and soft, only its inner half shows
    ink.smooth(outline, true)
    ink.stroke(tone(0.08), 1.6 * u, ghost() and 0.15 or 0.3, true)
    -- white streaks lifted out, fanning from the base
    local ns = o.streaks or (pointed and rng.int(3, 5) or rng.int(9, 13))
    for k = 1, ns do
      local f = (k - 0.5) / ns * 2 - 1 + rng.sym(0.05)
      local len = (pointed and rng.range(0.4, 0.85) or rng.range(0.35, 0.8)) * (1 - 0.35 * f * f)
      if pointed and k == (ns + 1) // 2 then f, len = 0, rng.range(0.8, 0.92) end
      local x1 = f * half(len) * 0.85 + bend * len * len
      local mx = f * half(len * 0.5) * 0.6 + rng.sym(0.02) + bend * len * len * 0.3
      streak3(f * 0.03, 0.0, mx * 0.5, len * 0.3, mx, len * 0.6, x1, len,
        (pointed and 0.6 or 1) * rng.range(0.022, 0.045), 0.002, white, rng.range(0.55, 0.9))
    end
    -- a few fine dark veins, following the petal
    if fine then
      for _ = 1, rng.int(4, 7) do
        local f = rng.sym(0.85)
        local v0, v1 = rng.range(0.2, 0.35), rng.range(0.75, 0.95)
        local x0, x1 = f * half(v0) * 0.7 + bend * v0 * v0, f * half(v1) * 0.9 + bend * v1 * v1
        ink.smooth(ink.sample(ink.bezier3(x0, v0, x0 + (x1 - x0) * 0.2, lerp(v0, v1, 0.4), x1 * 0.97, lerp(v0, v1, 0.75), x1, v1), 5), false)
        ink.stroke(tone(0.1), 0.15, rng.range(0.18, 0.32), true)
      end
    end
  ink.unclip()
  return outline
end

-- ---------------------------------------------------------------- flowers
-- the white star-shaped heart, stamens and a copper eye, at the origin; r = radius scale
local function heart(rng, np, r)
  for k = 1, 2 * np do
    local a = (k - 0.5) * 360 / (2 * np) + rng.sym(8)
    ink.push() ink.rotate(a)
    streak3(0, 0, 0.01, 0.1 * r, -0.01, 0.2 * r, 0, rng.range(0.24, 0.36) * r, 0.06 * r, 0.004 * r, white, 0.85)
    ink.pop()
  end
  ink.circle(0, 0, 0.13 * r) ink.fill(white, 0.9)
  if not ghost() then
    for _ = 1, 14 do
      local a, d = rng.range(0, 2 * pi), rng.range(0.05, 0.12) * r
      ink.moveto(0, 0) ink.lineto(d * cos(a), d * sin(a))
      ink.stroke(tone(0.1), 0.2, 0.7)
      ink.circle(d * cos(a), d * sin(a), 0.008 * r) ink.fill(tone(0.05), 0.9)
    end
  end
  ink.circle(0, 0, 0.042 * r) ink.fill(ink.accent(-0.15))
  ink.circle(0, 0, 0.022 * r) ink.fill(ink.accent(0.3))
end

-- Five broad petals seen from the front. s = petal length (cm); center at the origin.
function M.flower(rng, s, o)
  o = o or {}
  ink.push()
  ink.scale(s)
  ink.rotate(rng.range(0, 72))
  local np = o.petals or 5
  local t0 = o.tone or (rng.chance(0.25) and rng.range(0.2, 0.28) or rng.range(0.3, 0.46))
  for k = 0, np - 1 do
    ink.push()
    ink.rotate(k * 360 / np + rng.sym(6))
    ink.scale(rng.range(0.9, 1.06))
    ink.translate(0, 0.04)
    M.petal(rng, { tone = t0 + rng.sym(0.04) })
    ink.pop()
  end
  heart(rng, np, 1)
  ink.pop()
end

-- A star lily seen at a tilt: six pointed, recurved petals in a star that is
-- squashed along y, so the petals behind (pointing up) are short and darker and
-- the ones in front are long and pale; stamens stand out of the throat.
-- Center at the origin, the flower faces +y; s = petal length (cm).
function M.lily(rng, s, o)
  o = o or {}
  ink.push()
  ink.scale(s)
  local tilt = o.tilt or rng.range(0.45, 0.62)
  local spin = rng.range(0, 60)
  local t0 = o.tone or rng.range(0.30, 0.38)
  local order = {}
  for k = 0, 5 do order[#order + 1] = spin + k * 60 + rng.sym(8) end
  table.sort(order, function(a, b) return sin(a * rad) > sin(b * rad) end)  -- back petals first
  for _, a in ipairs(order) do
    local back = sin(a * rad)
    ink.push()
    ink.scale(1, tilt)
    ink.rotate(a - 90)
    ink.scale(rng.range(0.88, 1.05))
    M.petal(rng, { shape = "pointed", w = rng.range(0.11, 0.14), tone = t0 + 0.1 * back * -0.8 + rng.sym(0.03),
      bend = (rng.chance(0.5) and 1 or -1) * rng.range(0.04, 0.14), heart = false, streaks = rng.int(3, 4) })
    ink.pop()
  end
  -- pale throat
  for k = 1, 4 do
    ink.smooth(ink.blob(rng, 0, 0, 0.05 + 0.05 * k, (0.05 + 0.05 * k) * tilt, 0.2, 9), true)
    ink.fill(white, 0.22)
  end
  -- stamens: curved filaments, dark anthers, copper pollen
  if not ghost() then
    for k = 1, 6 do
      local a = (k - 3.5) * 16 + rng.sym(6)
      local L = rng.range(0.3, 0.48)
      local ex, ey = L * sin(a * rad), L * cos(a * rad)
      ink.smooth(ink.sample(ink.bezier3(0, 0, ex * 0.2, ey * 0.5, ex * 0.8, ey * 0.85, ex, ey), 6), false)
      ink.stroke(tone(0.12), 0.25, 0.85)
      ink.push() ink.translate(ex, ey) ink.rotate(-a + rng.sym(30))
      ink.smooth(ink.blob(rng, 0, 0, 0.022, 0.04, 0.1, 6), true) ink.fill(tone(0.05))
      ink.pop()
      if rng.chance(0.5) then ink.circle(ex + rng.sym(0.03), ey + rng.range(0.02, 0.05), 0.008) ink.fill(ink.accent(0)) end
    end
  end
  ink.circle(0, 0, 0.035) ink.fill(ink.accent(-0.2))
  ink.pop()
end

-- A small flower with round petals, seen from the front: violets, forget-me-nots.
-- r = radius (cm). Fewer layers than the large flower.
function M.blossom(rng, r, o)
  o = o or {}
  ink.push()
  ink.scale(r)
  ink.rotate(rng.range(0, 72))
  local t0 = o.tone or rng.range(0.30, 0.45)
  for k = 0, 4 do
    ink.push()
    ink.rotate(k * 72 + rng.sym(8))
    ink.scale(rng.range(0.9, 1.08))
    local hw = round_half(rng.range(0.36, 0.44))
    local outline = ink.blade(function(v) return 0, v end, 18, hw, hw)
    ink.smooth(outline, true) ink.fill(tone(t0 + rng.sym(0.05)))
    ink.smooth(outline, true) ink.clip()
      ink.smooth(ink.blob(rng, rng.sym(0.2), rng.range(0.5, 0.9), 0.35, 0.3, 0.3, 8), true)
      ink.fill(tone(t0 - 0.2), 0.3, true)
      streak3(0, 0, 0.02, 0.2, -0.02, 0.4, rng.sym(0.05), 0.55, 0.12, 0.01, white, 0.7)
      ink.smooth(outline, true) ink.stroke(tone(0.08), 1.2 * lod(), 0.25, true)
    ink.unclip()
    ink.pop()
  end
  ink.circle(0, 0, 0.22) ink.fill(white, 0.85)
  ink.circle(0, 0, 0.09) ink.fill(o.eye or tone(0.08))
  ink.pop()
end

-- A floret a few millimeters across: five petals, round (forget-me-not) or
-- pointed (star), one fill, a dark eye. r = radius (cm). Cheap: used by the hundred.
function M.floret(rng, r, o)
  o = o or {}
  local star = o.star
  if star == nil then star = rng.chance(0.5) end
  if r * lod() < 0.07 then
    local ph, pts = rng.range(0, 2 * pi), {}
    for k = 0, 9 do
      local a = ph + k * pi / 5
      local d = (k % 2 == 0) and r or r * (star and 0.32 or 0.62)
      pts[#pts + 1] = { d * cos(a), d * sin(a) }
    end
    ink.poly(pts, true) ink.fill(tone(o.tone or rng.range(0.22, 0.42)))
    local e = 0.2 * r
    ink.poly({ { e, 0 }, { 0, e }, { -e, 0 }, { 0, -e } }, true) ink.fill(o.eye or tone(0.05))
    return
  end
  local ph = rng.range(0, 2 * pi)
  for k = 0, 4 do
    local a = ph + k * 2 * pi / 5 + rng.sym(0.15)
    local c, s = cos(a), sin(a)
    local L = r * rng.range(0.85, 1.1)
    local w = star and 0.26 or 0.42
    local pts
    if star then
      pts = { { 0, 0 }, { 0.45 * L, w * L * 0.6 }, { L, 0 }, { 0.45 * L, -w * L * 0.6 } }
    else
      pts = { { 0, 0 }, { 0.3 * L, w * L }, { 0.85 * L, w * L * 0.8 }, { L, 0 }, { 0.85 * L, -w * L * 0.8 }, { 0.3 * L, -w * L } }
    end
    for i, p in ipairs(pts) do pts[i] = { p[1] * c - p[2] * s, p[1] * s + p[2] * c } end
    ink.smooth(pts, true, star and 0.5 or 1)
  end
  local t0 = o.tone or rng.range(0.22, 0.42)
  ink.fill(tone(t0))
  if r > 0.05 and not ghost() then
    ink.circle(0, 0, 0.35 * r) ink.fill(white, 0.75)
  end
  ink.circle(0, 0, 0.16 * r) ink.fill(o.eye or tone(0.05))
end

-- a closed bud on its own: teardrop, three sepals. Base at the origin, +y; s = length
function M.bud(rng, s, o)
  o = o or {}
  ink.push() ink.scale(s)
  local bend = rng.sym(0.1)
  local outline = ink.blade(function(v) return bend * v * v, v end, 18,
    function(v) return 0.3 * sin(pi * v ^ 0.6) ^ 0.8 end, function(v) return 0.3 * sin(pi * v ^ 0.6) ^ 0.8 end)
  local t0 = o.tone or rng.range(0.3, 0.42)
  ink.smooth(outline, true) ink.fill(tone(t0))
  ink.smooth(outline, true) ink.clip()
    mottle(rng, -0.3, 0, 0.3, 1, 5, 0.1, t0 - 0.2, t0 + 0.2, 0)
    streak3(-0.08, 0.05, -0.1, 0.35, -0.05, 0.65, bend * 0.8, 0.95, 0.06, 0.005, white, 0.7)
    ink.smooth(outline, true) ink.stroke(tone(0.06), 1.4 * lod(), 0.3, true)
  ink.unclip()
  for k = -1, 1 do
    local a = k * 24 + rng.sym(6)
    ink.push() ink.translate(k * 0.05, -0.02) ink.rotate(a) ink.scale(0.06, k == 0 and 0.22 or 0.32)
    ink.smooth(ink.blade(function(v) return -k * 0.4 * v * v, v end, 8, function(v) return sin(pi * v ^ 0.6) end, function(v) return sin(pi * v ^ 0.6) end), true)
    ink.pop()
  end
  ink.fill(tone(0.14), 0.9)
  ink.pop()
end

-- a bellflower hanging from the origin (it hangs along -y); s = length
function M.bell(rng, s, o)
  o = o or {}
  ink.push() ink.scale(s) ink.rotate(rng.sym(8))
  local t0 = o.tone or rng.range(0.3, 0.4)
  -- body: a flared tube with a three-lobed rim
  local rim = {}
  local pts = { { 0.12, -0.02 } }
  local function side(sg)
    local out = {}
    for i = 0, 10 do
      local v = i / 10
      out[#out + 1] = { sg * (0.12 + 0.22 * v ^ 1.4 + 0.08 * v ^ 6), -0.02 - 0.82 * v }
    end
    return out
  end
  local R, Lft = side(1), side(-1)
  pts = {}
  for _, p in ipairs(R) do pts[#pts + 1] = p end
  -- lobes along the rim from right to left, pointed tips
  local tips = { { 0.44, -0.98 }, { 0.12, -1.0 }, { -0.16, -1.0 }, { -0.44, -0.98 } }
  local sinus = { { 0.27, -0.86 }, { -0.02, -0.9 }, { -0.29, -0.86 } }
  pts[#pts + 1] = { tips[1][1] + rng.sym(0.03), tips[1][2] + rng.sym(0.03) }
  for i = 1, 3 do
    pts[#pts + 1] = { sinus[i][1], sinus[i][2] + rng.sym(0.02) }
    pts[#pts + 1] = { tips[i + 1][1] + rng.sym(0.03), tips[i + 1][2] + rng.sym(0.03) }
  end
  for i = #Lft, 1, -1 do pts[#pts + 1] = Lft[i] end
  ink.smooth(pts, true, 0.7) ink.fill(tone(t0))
  ink.smooth(pts, true, 0.7) ink.clip()
    mottle(rng, -0.5, -1.0, 0.5, 0, 10, 0.12, t0 - 0.2, t0 + 0.2, 10)
    for k = -2, 2 do
      local x = k * 0.1
      streak3(x * 0.3, -0.05, x * 0.8, -0.35, x * 1.3, -0.65, x * 1.9 + rng.sym(0.03), -0.92, 0.02, 0.012,
        k % 2 == 0 and white or tone(0.08), k % 2 == 0 and 0.55 or 0.3, k % 2 ~= 0)
    end
    ink.smooth(pts, true, 0.7) ink.stroke(tone(0.06), 1.5 * lod(), 0.3, true)
  ink.unclip()
  ink.smooth(pts, true, 0.7) ink.stroke(tone(0.08), 0.18, 0.35)
  -- calyx on top
  for k = -1, 1 do
    ink.push() ink.translate(0, 0.02) ink.rotate(180 + k * 40 + rng.sym(8)) ink.scale(0.08, 0.26)
    ink.smooth(ink.blade(function(v) return 0, v end, 8, function(v) return sin(pi * v ^ 0.7) end, function(v) return sin(pi * v ^ 0.7) end), true)
    ink.pop()
  end
  ink.fill(tone(0.1))
  ink.circle(0, 0.02, 0.06) ink.fill(tone(0.08))
  ink.pop()
end

-- ---------------------------------------------------------------- foliage
-- A leaf pointing +y, length 1, with a bent midrib, a darker half (the leaf
-- folds along its rib) and veins lifted out in white. With depth > 0 it is
-- lobed like acanthus: a narrow body plus pointed lobes leaning toward the
-- tip, all filled as one shape; with depth = 0 it is entire and finely toothed.
-- Opts: w (half-width of the envelope), lobes (per side), depth (0..1), bend, tone.
function M.leaf(rng, o)
  o = o or {}
  local W = o.w or rng.range(0.20, 0.27)
  local bend = o.bend or rng.sym(0.25)
  local lobes = o.lobes or rng.int(3, 5)
  local depth = o.depth or rng.range(0.3, 0.7)
  local t0 = o.tone or rng.range(0.26, 0.38)
  local u = lod()
  local fine = u > 0.6 and not ghost()
  local spine = function(v) return bend * v * v - 0.3 * bend * v, v end
  local function tangent(v)
    local x0, y0 = spine(max(0, v - 0.01)) local x1, y1 = spine(min(1, v + 0.01))
    local dx, dy = x1 - x0, y1 - y0 local L = sqrt(dx * dx + dy * dy)
    return dx / L, dy / L
  end
  local function envelope(v) return W * 2.3 * v ^ 0.55 * (1 - v) ^ 0.95 end
  local teeth = function(v) return 0.006 * (1 - abs(2 * ((v * 9) % 1) - 1)) end
  local veins = {}                       -- {x0,y0,x1,y1} lobe axes, for the white veins
  -- the body
  local bodyw = depth > 0 and (1 - 0.75 * depth) or 1
  local hb = function(v) return envelope(v) * bodyw end
  local outline = ink.blade(spine, u > 0.6 and 36 or 24, hb, hb, function(v) return (depth > 0 and 0 or 1) * teeth(v * 3) end)
  local shapes = { outline }
  -- the lobes
  if depth > 0 then
    for side = -1, 1, 2 do
      for k = 1, lobes do
        local v = 0.1 + 0.72 * (k - (side > 0 and 0.25 or 0.75)) / lobes
        local x0, y0 = spine(v)
        local tx, ty = tangent(v)
        local reach = envelope(min(0.95, v + 0.08)) * rng.range(0.95, 1.15)
        local ang = rng.range(38, 58) * rad
        -- lobe direction: the tangent turned outward by ang (side picks the side)
        local c, sn = cos(ang), sin(ang) * side
        local dx, dy = tx * c - ty * sn, tx * sn + ty * c
        local L = reach / sin(ang) * 0.95
        local lb = rng.sym(0.25) - side * 0.15
        local function ls(t) return x0 + dx * L * t - dy * lb * L * t * t, y0 + dy * L * t + dx * lb * L * t * t end
        local lw = function(t) return L * rng.range(0.26, 0.3) * sin(pi * t ^ 0.62) ^ 0.75 end
        local lobe = ink.blade(ls, 11, lw, lw, function(t, sd) return t > 0.2 and teeth(t * 1.4 + k) * L * 4 or 0 end)
        shapes[#shapes + 1] = lobe
        local mx, my = ls(0.45)
        local ex, ey = ls(0.92)
        veins[#veins + 1] = { x0, y0, mx, my, ex, ey }
      end
    end
  end
  local function trace() for _, sh in ipairs(shapes) do ink.smooth(sh, true, 0.8) end end
  trace() ink.fill(tone(t0))
  trace() ink.clip()
    -- the darker half
    local sd = rng.chance(0.5) and 1 or -1
    local hp = {}
    for i = 0, 30 do local x, y = spine(i / 30) hp[#hp + 1] = { x, y } end
    hp[#hp + 1] = { sd * 2, 1 } hp[#hp + 1] = { sd * 2, 0 }
    ink.poly(hp, true)
    ink.fill(tone(0.12), 0.28, true)
    mottle(rng, -W * 2.5, 0, W * 2.5, 1, fine and 13 or 6, 0.11, t0 - 0.2, t0 + 0.22, fine and 12 or 0)
    trace()
    ink.stroke(tone(0.06), 1.3 * u, 0.22, true)
    -- midrib and veins in white
    streak(spine, 10, 0.03, 0.003, white, 0.78)
    for _, vn in ipairs(veins) do
      local x0, y0, mx, my, ex, ey = vn[1], vn[2], vn[3], vn[4], vn[5], vn[6]
      streak3(x0, y0, mx, my, mx + (ex - mx) * 0.5, my + (ey - my) * 0.5, ex, ey, 0.017, 0.002, white, rng.range(0.5, 0.75))
    end
    if depth == 0 or #veins == 0 then
      for k = 1, 9 do
        local v = (k - 0.3) / 10 * 0.9
        local sg = (k % 2 == 0) and 1 or -1
        local x0, y0 = spine(v)
        local tx, ty = tangent(v)
        local nx, ny = -ty * sg, tx * sg
        local L = hb(v) * rng.range(0.75, 0.95)
        streak3(x0, y0, x0 + nx * L * 0.4, y0 + ny * L * 0.4, x0 + nx * L * 0.75 + tx * L * 0.3, y0 + ny * L * 0.75 + ty * L * 0.3,
          x0 + nx * L * 0.95 + tx * L * 0.6, y0 + ny * L * 0.95 + ty * L * 0.6, 0.014, 0.002, white, rng.range(0.45, 0.7))
      end
    end
  ink.unclip()
  if depth == 0 then
    ink.smooth(outline, true, 0.8)
    ink.stroke(tone(0.05), 0.18, ghost() and 0.15 or 0.4)
  end
end

-- A small entire leaf, cheap: for stem nodes and sprays. +y, length 1.
function M.leaflet(rng, o)
  o = o or {}
  local W = o.w or rng.range(0.16, 0.24)
  local bend = o.bend or rng.sym(0.2)
  local t0 = o.tone or rng.range(0.2, 0.34)
  local spine = function(v) return bend * v * v, v end
  local half = function(v) return W * 2.2 * v ^ 0.5 * (1 - v) ^ 0.9 end
  local outline, c, nrm = ink.blade(spine, 18, half, half)
  ink.smooth(outline, true) ink.fill(tone(t0))
  if lod() > 0.25 and not ghost() then
    ink.smooth(outline, true) ink.clip()
      local sd = rng.chance(0.5) and 1 or -1
      local hp = {}
      for i = 1, #c do hp[#hp + 1] = c[i] end
      for i = #c, 1, -1 do hp[#hp + 1] = { c[i][1] + sd * nrm[i][1], c[i][2] + sd * nrm[i][2] } end
      ink.poly(hp, true) ink.fill(tone(0.08), 0.3, true)
      streak(spine, 10, 0.03, 0.003, white, 0.65)
    ink.unclip()
  end
end

-- ---------------------------------------------------------------- stems and sprays
-- a tapered stem along points (local cm), full widths in cm at the base and the tip;
-- with `tip` (cm) its last stretch narrows to a point, as at a growing tip
function M.stem(pts, w0, w1, c, op, tip)
  local wbp = (w0 + w1) / 2 * ink.unit() * ink.CM
  if wbp < 0.7 then
    ink.smooth(pts, false)
    ink.stroke(c or tone(0.07), wbp, op)
    return
  end
  local width = function(t) return lerp(w0, w1, t) end
  if tip then
    local _, L = ink.arclen(pts)
    local f = math.min(1, tip / math.max(L, 1e-9))
    width = function(t) return lerp(w0, w1, t) * (t > 1 - f and lerp(1, 0.15, (t - 1 + f) / f) or 1) end
  end
  ink.smooth(ink.ribbon(pts, width), true)
  ink.fill(c or tone(0.07), op)
end

-- The path of a branch from a stem point (sx,sy) whose stem runs along (tx,ty)
-- to a motif at (bx,by) whose axis is (ax,ay): it leaves along the stem (or
-- against it, if the target lies behind), turned 28..48 degrees toward the
-- target, and arrives along the motif's axis. Returns sampled points.
function M.branch_path(rng, sx, sy, tx, ty, bx, by, ax, ay)
  local dx, dy = bx - sx, by - sy
  local d = sqrt(dx * dx + dy * dy)
  if tx * dx + ty * dy < -0.3 * d then tx, ty = -tx, -ty end
  local turn = (tx * dy - ty * dx > 0 and 1 or -1) * rng.range(28, 48) * rad
  local ox, oy = tx * cos(turn) - ty * sin(turn), tx * sin(turn) + ty * cos(turn)
  return ink.sample(ink.bezier3(sx, sy, sx + ox * d * 0.45, sy + oy * d * 0.45, bx - ax * d * 0.4, by - ay * d * 0.4, bx, by),
    max(6, floor(d / 0.15)))
end

-- integrate a path from a heading function: start (x,y), heading h(s) in degrees
-- at arclength s, total length L, n steps
local function walk(x, y, h, L, n)
  local pts, ds = { { x, y } }, L / n
  for i = 1, n do
    local a = h((i - 0.5) * ds) * rad
    x, y = x + ds * cos(a), y + ds * sin(a)
    pts[#pts + 1] = { x, y }
  end
  return pts
end
M.walk = walk

-- A forget-me-not cyme: a stem of length L (cm) that curls at its end like a
-- scorpion's tail, florets crowding along it and shrinking into buds; often a
-- second, shorter curl forks off. Starts at the origin heading +y; side = +1
-- curls left, -1 right.
local function curl(rng, x, y, h0, L, side, t0, wbase)
  local turn = rng.range(170, 270)
  local N = 36
  local pts = walk(x, y, function(s) return h0 + side * turn * (s / L) ^ 2.3 end, L, N)
  M.stem(pts, wbase, 0.006, tone(0.1))
  local nrm = ink.normals(pts)
  local n = rng.int(11, 17)
  for k = 1, n do
    local f = 0.18 + 0.82 * (k / n) ^ 0.75
    local i = max(2, min(#pts, floor(f * N + 1.5)))
    local sg = (k % 2 == 0) and 1 or -1
    local px, py = pts[i][1], pts[i][2]
    local stalk = lerp(0.1, 0.02, f) * rng.range(0.7, 1.2)
    local qx, qy = px + nrm[i][1] * sg * stalk, py + nrm[i][2] * sg * stalk
    if stalk > 0.03 then ink.moveto(px, py) ink.lineto(qx, qy) ink.stroke(tone(0.12), 0.25, 0.9) end
    local r = lerp(0.115, 0.03, f) * rng.range(0.85, 1.15)
    ink.push() ink.translate(qx, qy)
    if f > 0.8 then
      ink.circle(0, 0, r * 0.6) ink.fill(tone(t0 - 0.06))
    else
      M.floret(rng, r, { star = false, tone = t0 + rng.sym(0.08) })
    end
    ink.pop()
  end
  return pts
end

function M.cyme(rng, L, o)
  o = o or {}
  local side = o.side or (rng.chance(0.5) and 1 or -1)
  local t0 = rng.range(0.22, 0.36)
  local pts = curl(rng, 0, 0, 90 + rng.sym(10), L, side, t0, 0.026)
  if (o.fork ~= false) and rng.chance(o.fork and 1 or 0.6) then
    local i = floor(#pts * rng.range(0.25, 0.4))
    local a = pts[i + 1] local b = pts[i]
    local h = math.atan(a[2] - b[2], a[1] - b[1]) / rad
    curl(rng, b[1], b[2], h - side * rng.range(30, 50), L * rng.range(0.45, 0.65), -side, t0 + 0.04, 0.018)
  end
end

-- A wiry branching sprig (baby's breath): forks two or three ways `depth`
-- times, small leaves at the lower forks, florets and buds at the tips.
-- Starts at the origin heading +y, length L (cm).
function M.sprig(rng, L, o)
  o = o or {}
  local depth = o.depth or 4
  local t0 = rng.range(0.22, 0.4)
  local function branch(x, y, a, len, d, w)
    local bend = rng.sym(20)
    local pts = walk(x, y, function(s) return a + bend * s / len end, len, 6)
    M.stem(pts, w, w * 0.7, tone(0.1))
    local ex, ey = pts[#pts][1], pts[#pts][2]
    local ea = a + bend
    if d == 0 then
      ink.push() ink.translate(ex, ey)
      if rng.chance(0.7) then M.floret(rng, rng.range(0.045, 0.075), { tone = t0 + rng.sym(0.08) })
      else ink.circle(0, 0, rng.range(0.018, 0.028)) ink.fill(tone(t0 - 0.05)) end
      ink.pop()
      return
    end
    if d >= depth - 1 and rng.chance(0.7) then
      local sg = rng.chance(0.5) and 1 or -1
      ink.push() ink.translate(ex, ey) ink.rotate(ea - 90 + sg * rng.range(40, 70)) ink.scale(len * rng.range(0.5, 0.8))
      M.leaflet(rng, { w = 0.14 })
      ink.pop()
    end
    local kids = rng.chance(0.25) and 3 or 2
    for k = 1, kids do
      local da = (kids == 2) and (k == 1 and -1 or 1) * rng.range(16, 34) or (k - 2) * rng.range(22, 36)
      branch(ex, ey, ea + da, len * rng.range(0.58, 0.74), d - 1, w * 0.72)
    end
  end
  branch(0, 0, 90 + rng.sym(8), L * 0.36, depth, 0.024)
end

-- Queen Anne's lace: rays fanning upward, each ending in a small umbel of starry
-- florets; bracts at the base. R = reach (cm); base at the origin.
function M.umbel(rng, R, o)
  local nr = rng.int(9, 13)
  for k = 1, nr do
    local a = 90 + (k - (nr + 1) / 2) * (110 / nr) + rng.sym(4)
    local L = R * rng.range(0.78, 1.0) * (1 - 0.15 * abs(a - 90) / 55)
    local ex, ey = L * cos(a * rad), L * sin(a * rad)
    ink.smooth(ink.sample(ink.bezier3(0, 0, ex * 0.15, ey * 0.5, ex * 0.6, ey * 0.95, ex, ey), 6), false)
    ink.stroke(tone(0.12), 0.25, 0.9)
    local ns = rng.int(5, 8)
    for j = 1, ns do
      local b = a + (j - (ns + 1) / 2) * 16 + rng.sym(5)
      local l = R * rng.range(0.12, 0.2)
      local fx, fy = ex + l * cos(b * rad), ey + l * sin(b * rad)
      ink.moveto(ex, ey) ink.lineto(fx, fy) ink.stroke(tone(0.14), 0.18, 0.85)
      ink.push() ink.translate(fx, fy)
      M.floret(rng, R * rng.range(0.035, 0.05), { star = true, tone = rng.range(0.25, 0.42) })
      ink.pop()
    end
  end
  for k = -1, 1 do
    ink.push() ink.rotate(k * 40 + rng.sym(10) + 180) ink.scale(R * rng.range(0.15, 0.22))
    M.leaflet(rng, { w = 0.06, bend = k * 0.2 })
    ink.pop()
  end
end

-- A flower gone to seed, a dandelion clock: hairline rays from a small dark
-- head, each ending in a tuft, a few gaps where seeds have gone, and a few
-- seeds drifting away up and to one side. Center at the origin; r = radius (cm).
local function tuft(x, y, a, l)
  for j = -2, 2 do
    local b = a + j * 0.32
    ink.moveto(x, y) ink.lineto(x + l * cos(b), y + l * sin(b))
  end
end
function M.seedhead(rng, r, o)
  o = o or {}
  local fine = lod() * r > 0.2 and not ghost()
  local n = fine and rng.int(26, 34) or 16
  local gone = rng.range(0, 2 * pi)
  for k = 1, n do
    local a = 2 * pi * (k + rng.sym(0.3)) / n
    if not (abs(((a - gone + pi) % (2 * pi)) - pi) < 0.5 and rng.chance(0.7)) then
      local L = r * rng.range(0.72, 0.86)
      local c, s = cos(a), sin(a)
      ink.moveto(0.1 * r * c, 0.1 * r * s) ink.lineto(L * c, L * s)
      if fine then tuft(L * c, L * s, a, r * rng.range(0.14, 0.2)) end
    end
  end
  ink.stroke(tone(0.16), 0.22, 0.85)
  ink.circle(0, 0, 0.13 * r) ink.fill(tone(0.12))
  if fine then
    for _ = 1, 10 do speck(rng.sym(0.08 * r), rng.sym(0.08 * r), 0.03 * r, rng.range(0, pi)) end
    ink.fill(tone(0.04), 0.8)
  end
  -- drifting seeds: an achene on a beak, the tuft above it
  local side = o.side or (rng.chance(0.5) and 1 or -1)
  for _ = 1, o.drift or rng.int(2, 4) do
    local d = r * rng.range(1.3, 2.4)
    local a = (90 - side * rng.range(15, 60)) * rad
    local x, y = d * cos(a), d * sin(a)
    local tilt = (90 + rng.sym(35)) * rad
    local l = r * 0.32
    local tx, ty = x + l * cos(tilt), y + l * sin(tilt)
    ink.moveto(x, y) ink.lineto(tx, ty)
    tuft(tx, ty, tilt, r * 0.17)
    ink.stroke(tone(0.18), 0.2, 0.8)
    ink.push() ink.translate(x, y) ink.rotate(tilt / rad - 90)
    ink.smooth(ink.blade(function(v) return 0, -0.12 * r * v end, 6, function(v) return 0.025 * r * sin(pi * v) end,
      function(v) return 0.025 * r * sin(pi * v) end), true)
    ink.fill(tone(0.1))
    ink.pop()
  end
end

-- a tapered logarithmic spiral, s = size (cm); starts at the origin, outer end
function M.tendril(rng, s)
  local pts = {}
  local turns = rng.range(1.6, 2.3)
  for i = 0, 50 do
    local t = i / 50
    local a = t * turns * 2 * pi
    local r = s * (1 - 0.92 * t) ^ 1.6
    pts[#pts + 1] = { r * cos(a) - s, r * sin(a) }
  end
  M.stem(pts, 0.022, 0.004, tone(0.12))
end

-- ---------------------------------------------------------------- accents (copper hairlines)
-- a four-point star with a hairline cross; r = radius (cm)
function M.sparkle(rng, r, o)
  o = o or {}
  local c = o.color or ink.accent(0)
  local k = 0.12
  ink.poly({ { 0, r }, { k * r, k * r }, { r * 0.75, 0 }, { k * r, -k * r }, { 0, -r }, { -k * r, -k * r }, { -r * 0.75, 0 }, { -k * r, k * r } }, true)
  ink.fill(c)
  if o.rays ~= false then
    ink.moveto(0, r * 1.15) ink.lineto(0, r * 1.7) ink.moveto(0, -r * 1.15) ink.lineto(0, -r * 1.7)
    ink.stroke(c, 0.2, 0.8)
    ink.circle(0, r * 1.9, r * 0.07) ink.circle(0, -r * 1.9, r * 0.07) ink.fill(c, 0.8)
  end
end

-- a tiny hairline quatrefoil with a dot; r = radius (cm)
function M.rosette(rng, r, o)
  local c = (o and o.color) or ink.accent(0)
  for k = 0, 3 do
    local a = k * pi / 2 + pi / 4
    ink.circle(r * 0.5 * cos(a), r * 0.5 * sin(a), r * 0.42)
  end
  ink.stroke(c, 0.22, 0.85)
  ink.circle(0, 0, r * 0.14) ink.fill(c)
  ink.moveto(0, r * 1.05) ink.lineto(0, r * 1.5) ink.moveto(0, -r * 1.05) ink.lineto(0, -r * 1.5)
  ink.stroke(c, 0.2, 0.7)
end

-- the header fleuron: a printer's ivy leaf (hedera) in copper, tip down-left,
-- its stem curling once and running out to the right, where the head rule
-- continues. Origin at the leaf's notch; returns the end of the stem in page cm.
function M.hedera(rng, s, o)
  local c = (o and o.color) or ink.accent(0)
  ink.push() ink.scale(s)
  local pts = {}
  for i = 0, 47 do
    local t = i / 48 * 2 * pi
    local x = 16 * sin(t) ^ 3
    local y = 13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t)
    pts[#pts + 1] = { x / 17, (y - 5) / 17 }      -- notch at the origin, tip at (0,-1.3)
  end
  ink.push() ink.rotate(-38)
  ink.smooth(pts, true) ink.fill(c)
  -- veins scratched out of the copper
  ink.moveto(0, -0.05) ink.curveto(0.02, -0.4, -0.02, -0.8, 0, -1.12)
  ink.moveto(0, -0.35) ink.curveto(0.15, -0.38, 0.3, -0.32, 0.42, -0.22)
  ink.moveto(0, -0.35) ink.curveto(-0.15, -0.38, -0.3, -0.32, -0.42, -0.22)
  ink.stroke(ink.paper, 0.35)
  ink.pop()
  -- stem: up out of the notch, one curl, then away to the right
  local stem = { { 0, 0 }, { 0.12, 0.28 }, { 0.38, 0.42 }, { 0.6, 0.3 }, { 0.52, 0.1 }, { 0.36, 0.2 }, { 0.48, 0.36 }, { 0.85, 0.36 }, { 1.4, 0.3 }, { 2.0, 0.28 } }
  M.stem(stem, 0.05, 0.012, c)
  ink.circle(-0.25, 0.42, 0.04) ink.circle(0.95, 0.6, 0.035) ink.circle(0.7, -0.05, 0.03) ink.fill(c, 0.85)
  local rx, ry = ink.to_page(2.0, 0.28)
  ink.pop()
  return rx, ry
end

-- ---------------------------------------------------------------- visitors
local function ellipse(cx, cy, rx, ry, n)
  local pts = {}
  for i = 0, n - 1 do local a = 2 * pi * i / n pts[#pts + 1] = { cx + rx * cos(a), cy + ry * sin(a) } end
  return pts
end

-- one wing (or any flat shape) painted like a petal: wash, blotches, a dark
-- pooled border, white veins fanning from the root (rx, ry), pale spots at the rim
local function wing(rng, pts, t0, rx, ry, spots, fine)
  ink.smooth(pts, true) ink.fill(tone(t0))
  ink.smooth(pts, true) ink.clip()
    mottle(rng, -1.2, -1.2, 1.2, 1.2, fine and 9 or 4, 0.14, t0 - 0.2, t0 + 0.2, fine and 8 or 0)
    ink.smooth(pts, true) ink.stroke(tone(0.05), 0.26 * lod() * ink.CM, ghost() and 0.25 or 0.55, true)
    for i, p in ipairs(pts) do
      local f = rng.range(0.7, 0.88)
      local ex, ey = rx + (p[1] - rx) * f, ry + (p[2] - ry) * f
      streak3(rx, ry, lerp(rx, ex, 0.3), lerp(ry, ey, 0.4), lerp(rx, ex, 0.7), lerp(ry, ey, 0.75), ex, ey,
        0.035, 0.004, white, rng.range(0.35, 0.6))
      if spots and fine and i > 1 and i < #pts then
        local cx, cy = rx + (p[1] - rx) * 0.9, ry + (p[2] - ry) * 0.9
        ink.circle(cx, cy, rng.range(0.025, 0.04)) ink.fill(white, 0.8)
      end
    end
  ink.unclip()
end

-- A butterfly seen from above, wings spread, head toward +y, the body's center at
-- the origin; s = wingspan (cm). o.open in (0,1] narrows the wings: a wingbeat.
function M.butterfly(rng, s, o)
  o = o or {}
  local open = o.open or 1
  ink.push() ink.scale(s / 2)                       -- one unit = half the span
  local fine = lod() > 0.3 and not ghost()
  local t0 = o.tone or rng.range(0.28, 0.4)
  local FW = { { 0.05, 0.1 }, { 0.3, 0.45 }, { 0.65, 0.68 }, { 0.92, 0.66 }, { 1.0, 0.5 }, { 0.88, 0.25 }, { 0.55, 0.05 }, { 0.15, -0.02 } }
  local HW = { { 0.06, -0.02 }, { 0.45, -0.02 }, { 0.72, -0.22 }, { 0.7, -0.5 }, { 0.5, -0.72 }, { 0.25, -0.7 }, { 0.08, -0.35 } }
  for _, w in ipairs({ FW, HW }) do for _, p in ipairs(w) do p[1], p[2] = p[1] + rng.sym(0.03), p[2] + rng.sym(0.03) end end
  local eye = rng.chance(0.7)
  for _, sx in ipairs({ -1, 1 }) do
    local function side(w) local out = {} for i, p in ipairs(w) do out[i] = { sx * p[1] * open, p[2] } end return out end
    wing(rng, side(HW), t0 + 0.06, sx * 0.04 * open, -0.04, true, fine)
    if eye and fine then                                -- an eyespot with a copper pupil
      local ex, ey = sx * 0.43 * open, -0.42
      ink.smooth(ellipse(ex, ey, 0.11 * open, 0.11, 10), true) ink.fill(tone(0.08), 0.85)
      ink.smooth(ellipse(ex, ey, 0.07 * open, 0.07, 10), true) ink.fill(white, 0.85)
      ink.smooth(ellipse(ex, ey, 0.035 * open, 0.035, 8), true) ink.fill(ink.accent(0))
    end
  end
  for _, sx in ipairs({ -1, 1 }) do
    local w = {}
    for i, p in ipairs(FW) do w[i] = { sx * p[1] * open, p[2] } end
    wing(rng, w, t0, sx * 0.04 * open, 0.04, true, fine)
  end
  -- body: abdomen, furry thorax, head, clubbed antennae
  local hb = function(v) return 0.05 * sin(pi * v ^ 0.7) end
  ink.smooth(ink.blade(function(v) return 0, -0.62 + 0.62 * v end, 10, hb, hb), true) ink.fill(tone(0.06))
  ink.smooth(ellipse(0, 0.08, 0.075, 0.13, 10), true) ink.fill(tone(0.04))
  ink.circle(0, 0.27, 0.06) ink.fill(tone(0.04))
  if fine then
    for _, sx in ipairs({ -1, 1 }) do
      local ex, ey = sx * rng.range(0.22, 0.3), rng.range(0.78, 0.9)
      ink.moveto(sx * 0.02, 0.31) ink.curveto(sx * 0.05, 0.5, ex * 0.6, ey * 0.9, ex, ey)
      ink.stroke(tone(0.08), 0.35)
      ink.circle(ex, ey, 0.025) ink.fill(tone(0.06))
    end
    streak3(-0.015, -0.55, -0.02, -0.35, -0.02, -0.1, -0.01, 0.0, 0.015, 0.004, white, 0.45)
  end
  ink.pop()
end

-- A bee from above, head toward +y, center at the origin; s = body length (cm).
-- o.trail: a dotted flight path looping away behind it.
function M.bee(rng, s, o)
  o = o or {}
  ink.push() ink.scale(s)
  local fine = lod() > 0.25 and not ghost()
  if o.trail ~= false and not ghost() then
    local R, c, turns = 0.32, rng.range(0.16, 0.22), rng.range(1.2, 1.6)
    local side = rng.chance(0.5) and 1 or -1
    local pts = {}
    for i = 0, 60 do
      local th = i / 60 * turns * 2 * pi
      pts[#pts + 1] = { side * R * sin(th), -0.62 - c * th + R * (cos(th) - 1) * 0.6 }
    end
    ink.smooth(pts, false)
    ink.stroke(tone(0.18), 0.9, 0.7, false, "[0 2.6] 0")
  end
  -- abdomen with dark bands, a sting
  local ab = ellipse(0, -0.2, 0.19, 0.3, 16)
  ink.smooth(ab, true) ink.fill(tone(0.38))
  ink.smooth(ab, true) ink.clip()
    for k = 0, 2 do
      local y = -0.06 - 0.14 * k
      ink.poly({ { -0.3, y + 0.035 }, { 0, y + 0.06 }, { 0.3, y + 0.035 }, { 0.3, y - 0.035 }, { 0, y - 0.01 }, { -0.3, y - 0.035 } }, true)
    end
    ink.fill(tone(0.05), 0.9)
    if fine then mottle(rng, -0.2, -0.5, 0.2, 0.1, 4, 0.06, 0.2, 0.55, 4) end
    ink.smooth(ab, true) ink.stroke(tone(0.05), 0.12 * lod() * ink.CM, 0.4, true)
    streak3(-0.1, -0.38, -0.13, -0.25, -0.12, -0.12, -0.08, 0.0, 0.04, 0.008, white, 0.55)
  ink.unclip()
  ink.poly({ { -0.025, -0.48 }, { 0, -0.58 }, { 0.025, -0.48 } }, true) ink.fill(tone(0.05))
  -- legs, then a furry thorax and the head
  if fine then
    for _, sx in ipairs({ -1, 1 }) do
      for k = 0, 2 do
        local y0 = 0.17 - 0.06 * k
        local ex, ey = sx * rng.range(0.26, 0.32), y0 - 0.12 + 0.08 * (1 - k) + rng.sym(0.03)
        ink.moveto(sx * 0.08, y0) ink.curveto(sx * 0.18, y0 + 0.04, ex * 0.9, ey + 0.05, ex, ey)
      end
    end
    ink.stroke(tone(0.08), 0.35)
  end
  ink.smooth(ink.blob(rng, 0, 0.15, 0.14, 0.13, 0.18, 12), true) ink.fill(tone(0.06))
  if fine then mottle(rng, -0.14, 0.03, 0.14, 0.28, 3, 0.05, 0.02, 0.3, 6) end
  ink.smooth(ellipse(0, 0.33, 0.09, 0.075, 10), true) ink.fill(tone(0.04))
  for _, sx in ipairs({ -1, 1 }) do
    ink.moveto(sx * 0.03, 0.38) ink.lineto(sx * 0.07, 0.48) ink.lineto(sx * 0.14, 0.53)
  end
  ink.stroke(tone(0.06), 0.3)
  -- wings over the body: clear, veined, a little blue
  for _, sx in ipairs({ -1, 1 }) do
    for k, wl in ipairs({ { 0.5, 0.16, 32 }, { 0.36, 0.12, 52 } }) do
      ink.push() ink.translate(sx * 0.07, 0.17 - 0.04 * k) ink.rotate(sx > 0 and -wl[3] or 180 + wl[3])
      local w = ellipse(wl[1] / 2, 0, wl[1] / 2, wl[2] / 2, 14)
      ink.smooth(w, true) ink.fill(tone(0.85), 0.55)
      ink.smooth(w, true) ink.stroke(tone(0.15), 0.3, 0.75)
      if fine then
        ink.moveto(0.02, 0) ink.curveto(wl[1] * 0.3, 0.02, wl[1] * 0.6, 0.01, wl[1] * 0.85, 0)
        ink.moveto(wl[1] * 0.3, 0.01) ink.lineto(wl[1] * 0.55, wl[2] * 0.4)
        ink.stroke(tone(0.2), 0.2, 0.6)
      end
      ink.pop()
    end
  end
  ink.pop()
end

-- A snail crawling up along +y, its foot on the y axis and its shell on the +x
-- side, origin at the middle of the foot; s = shell diameter (cm).
function M.snail(rng, s, o)
  o = o or {}
  ink.push() ink.scale(s)
  local fine = lod() > 0.25 and not ghost()
  -- the body: a long soft foot, the head raised at the front
  local body = { { 0.0, -0.78 }, { -0.01, -0.3 }, { 0.0, 0.3 }, { 0.04, 0.58 }, { 0.12, 0.7 }, { 0.22, 0.66 },
    { 0.24, 0.5 }, { 0.2, 0.32 }, { 0.17, 0.0 }, { 0.12, -0.45 }, { 0.05, -0.7 } }
  for _, p in ipairs(body) do p[1] = p[1] * (1 + rng.sym(0.08)) end
  local tb = o.tone or rng.range(0.5, 0.6)
  ink.smooth(body, true) ink.fill(tone(tb))
  ink.smooth(body, true) ink.clip()
    if fine then mottle(rng, -0.1, -0.8, 0.3, 0.8, 5, 0.1, tb - 0.25, tb + 0.15, 10) end
    ink.moveto(-0.05, -0.8) ink.lineto(-0.05, 0.7) ink.lineto(0.04, 0.7) ink.lineto(0.04, -0.8) ink.close()
    ink.fill(tone(0.15), 0.35, true)
    ink.smooth(body, true) ink.stroke(tone(0.08), 0.1 * lod() * ink.CM, 0.4, true)
  ink.unclip()
  -- feelers: two long ones with eyes, two short ones
  for k, f in ipairs({ { 0.17, 0.66, 0.36, 1.02 }, { 0.1, 0.7, 0.18, 1.04 }, { 0.05, 0.68, 0.0, 0.84 } }) do
    ink.moveto(f[1], f[2]) ink.curveto(f[1] + 0.02, f[2] + 0.12, f[3] - 0.04, f[4] - 0.1, f[3], f[4])
    ink.stroke(tone(0.12), k < 3 and 0.45 or 0.35)
    if k < 3 then ink.circle(f[3], f[4], 0.028) ink.fill(tone(0.05)) end
  end
  -- the shell: a disc with a white spiral lifted out of it and a dark one beside it
  local cx, cy, R = 0.36, 0.0, 0.42
  local t0 = rng.range(0.22, 0.32)
  local disc = ink.blob(rng, cx, cy, R, R * 0.96, 0.03, 16)
  ink.smooth(disc, true) ink.fill(tone(t0))
  ink.smooth(disc, true) ink.clip()
    mottle(rng, cx - R, cy - R, cx + R, cy + R, fine and 7 or 3, 0.1, t0 - 0.18, t0 + 0.22, fine and 10 or 0)
    local turns, ph = rng.range(2.3, 2.7), rng.range(0, 2 * pi)
    local sp, dk = {}, {}
    for i = 0, 50 do
      local t = i / 50
      local a = ph + t * turns * 2 * pi
      local r = R * 0.95 * t ^ 1.15
      sp[#sp + 1] = { cx + r * cos(a), cy + r * sin(a) }
      local r2 = R * 0.95 * max(0, t - 0.12) ^ 1.15
      dk[#dk + 1] = { cx + r2 * cos(a), cy + r2 * sin(a) }
    end
    ink.smooth(dk, false) ink.stroke(tone(0.05), 0.07 * lod() * ink.CM, 0.6, true)
    ink.smooth(sp, false) ink.stroke(white, 0.05 * lod() * ink.CM, 0.75)
    ink.smooth(disc, true) ink.stroke(tone(0.05), 0.12 * lod() * ink.CM, 0.5, true)
  ink.unclip()
  ink.pop()
end

-- A small songbird perched, seen from the side, facing +x (o.facing = -1: -x);
-- its feet at the origin, s = length from tail to beak (cm).
function M.bird(rng, s, o)
  o = o or {}
  ink.push() ink.scale((o.facing or 1) * s, s)
  local fine = lod() > 0.3 and not ghost()
  local t0 = o.tone or rng.range(0.3, 0.38)
  -- the tail: a few long feathers fanning down and back
  local hw = function(v) return 0.055 * sin(pi * v ^ 0.4) ^ 0.6 end
  for k = 1, 4 do
    local L = rng.range(0.42, 0.5)
    ink.push() ink.translate(-0.26, 0.28) ink.rotate(rng.range(-150, -140) + 7 * k - 90)
    local f = ink.blade(function(v) return 0, v * L end, 10, hw, hw)
    ink.smooth(f, true) ink.fill(tone(0.12 + 0.05 * k))
    ink.smooth(f, true) ink.stroke(tone(0.05), 0.3, 0.5)
    ink.pop()
  end
  -- body and head in one outline
  local body = { { 0.37, 0.56 }, { 0.3, 0.665 }, { 0.15, 0.64 }, { -0.03, 0.54 }, { -0.22, 0.4 }, { -0.31, 0.3 },
    { -0.27, 0.22 }, { -0.08, 0.12 }, { 0.12, 0.12 }, { 0.27, 0.27 }, { 0.35, 0.42 } }
  for _, p in ipairs(body) do p[1], p[2] = p[1] + rng.sym(0.012), p[2] + rng.sym(0.012) end
  ink.smooth(body, true) ink.fill(tone(t0))
  ink.smooth(body, true) ink.clip()
    -- pale breast with darker specks, a darker cap
    for k = 1, 4 do
      ink.smooth(ink.blob(rng, 0.17, 0.27, 0.08 + 0.04 * k, 0.06 + 0.03 * k, 0.2, 9), true)
      ink.fill(white, 0.2)
    end
    mottle(rng, -0.35, 0.1, 0.4, 0.7, fine and 10 or 4, 0.07, t0 - 0.2, t0 + 0.2, fine and 10 or 0)
    if fine then
      for _ = 1, 14 do
        local x, y = rng.range(0.08, 0.3), rng.range(0.16, 0.42)
        ink.push() ink.translate(x, y) ink.rotate(rng.range(-20, 20))
        ink.smooth(ellipse(0, 0, 0.012, 0.022, 6), true)
        ink.pop()
      end
      ink.fill(tone(0.1), 0.7)
    end
    ink.smooth(ink.blob(rng, 0.24, 0.66, 0.15, 0.08, 0.1, 9), true) ink.fill(tone(0.08), 0.6, true)
    ink.smooth(body, true) ink.stroke(tone(0.05), 0.07 * lod() * ink.CM, 0.5, true)
  ink.unclip()
  -- the folded wing: a dark blade with feather tips, white lifted along the feathers
  local wingpts = { { 0.17, 0.47 }, { 0.04, 0.52 }, { -0.12, 0.45 }, { -0.28, 0.33 }, { -0.44, 0.22 }, { -0.35, 0.23 },
    { -0.38, 0.19 }, { -0.26, 0.21 }, { -0.28, 0.17 }, { -0.12, 0.23 }, { 0.05, 0.31 }, { 0.15, 0.4 } }
  local tw = t0 - 0.1
  ink.smooth(wingpts, true, 0.8) ink.fill(tone(tw))
  ink.smooth(wingpts, true, 0.8) ink.clip()
    mottle(rng, -0.45, 0.15, 0.2, 0.6, fine and 6 or 3, 0.07, tw - 0.15, tw + 0.2, 0)
    for k = 1, 5 do
      local y = 0.28 + 0.04 * k
      streak3(0.12, y + 0.05, 0.0, y + 0.03, -0.15, y - 0.03, -0.3 - 0.02 * k, y - 0.1 - 0.01 * k, 0.025, 0.003, white, rng.range(0.45, 0.7))
    end
    ink.smooth(wingpts, true, 0.8) ink.stroke(tone(0.04), 0.06 * lod() * ink.CM, 0.5, true)
  ink.unclip()
  -- beak, eye, legs
  ink.poly({ { 0.355, 0.585 }, { 0.47, 0.545 }, { 0.36, 0.51 } }, true) ink.fill(tone(0.05))
  ink.moveto(0.36, 0.548) ink.lineto(0.45, 0.546) ink.stroke(white, 0.2, 0.6)
  ink.circle(0.285, 0.585, 0.03) ink.fill(white, 0.95)
  ink.circle(0.29, 0.585, 0.018) ink.fill(tone(0.03))
  ink.circle(0.284, 0.592, 0.006) ink.fill(white)
  for _, lx in ipairs({ 0.0, 0.08 }) do
    ink.moveto(lx + 0.02, 0.14) ink.lineto(lx, 0.0)
    ink.moveto(lx - 0.05, 0.0) ink.lineto(lx + 0.05, 0.005)
  end
  ink.stroke(tone(0.06), 0.45)
  ink.pop()
end

-- draw `fn` as a pale ghost (the faded layer behind the garden)
function M.ghost(level, fn)
  local old = ink.set_lift(level or 0.62)
  fn()
  ink.set_lift(old)
end

return M
