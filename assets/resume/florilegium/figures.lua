-- figures.lua -- mathematical figures for florilegium's themes, drawn with ink.lua.
-- Copyright (c) 2026 Kevin Raymond. MIT License: see LICENSE or florilegium.sty.
--
-- Line drawings in the ink with a pale wash, the copper kept for a focus or a guide
-- line. Each figure draws inside a disc of radius R (cm) around the origin.
--   figures    FIG[name] = { pick(layout) -> parameters, draw(rng, R, p), caption(p),
--              w, max, r = {Rmin, Rmax} }: Maurer rose, hypotrochoid, Lissajous
--              curve, Platonic solid, knot, Apollonian gasket, Koch snowflake, Hilbert
--              curve, chords k -> mk mod n, golden rectangles, parabola, Petersen
--              graph, Vogel's disc, Fay's butterfly
--   families   FAM[name] = { values, label(v), title(p), pick(layout), draw(rng, R, v, p) }:
--              one parameter changing from figure to figure (the Koch snowflake one
--              level at a time, the cube truncated into the octahedron, ...)
--   helpers    maurer, phyllotaxis, fay, vogel; hull_of, truncate, solid (convex
--              solids in wireframe); compass (a fleuron for the header); caption_width
-- theme-math.lua builds its margin from these; theme-geometric.lua borrows a few.

local ink = require("ink")
local flora = require("flora")
local M = {}

local sin, cos, sqrt, exp, pi, abs, floor, max, min = math.sin, math.cos, math.sqrt, math.exp, math.pi, math.abs, math.floor, math.max, math.min
local tone, white = ink.tone, ink.white
local rad = pi / 180
local PHI = (1 + sqrt(5)) / 2
local GOLDEN = pi * (3 - sqrt(5))             -- 137.5°: 360° divided in the golden ratio
local function lerp(a, b, t) return a + (b - a) * t end
local function ghost() return ink.get_lift() > 0.3 end
local function gcd(a, b) while b ~= 0 do a, b = b, a % b end return a end
local function ink_line() return tone(0.08) end

-- a small seed or floret: a hexagon of radius r, a corner along angle a (radians)
local function seed(x, y, r, a)
  local pts = {}
  for k = 0, 5 do local b = a + k * pi / 3 pts[k + 1] = { x + r * cos(b), y + r * sin(b) } end
  ink.poly(pts, true)
end

-- ---------------------------------------------------------------- curves
-- r = cos(kθ) with k = n/d in lowest terms has N lobes (n of them if n·d is odd,
-- 2n if it is even), centered every 360°/N, each r = cos(kφ) for |φ| <= 90°/k.
-- When the lobes are wider than their spacing they overlap.
local function nlobes(n, d) return (n * d) % 2 == 1 and n or 2 * n end
-- one lobe pointing +y, length 1, as a closed outline through the origin
local function lobe(k, m)
  local pts, h = {}, pi / (2 * k)
  for i = 0, m - 1 do
    local p = -h + 2 * h * i / m
    local r = cos(k * p)
    pts[#pts + 1] = { -r * sin(p), r * cos(p) }
  end
  return pts
end

-- ---------------------------------------------------------------- the golden angle
-- Vogel's model of a sunflower head: floret i (1..N) at radius R·√((i-½)/N) and
-- angle i·137.5°; returns {x, y, r/R, angle}
local function vogel(N, R, spin)
  local out = {}
  for i = 1, N do
    local a = spin + i * GOLDEN
    local q = sqrt((i - 0.5) / N)
    out[i] = { R * q * cos(a), R * q * sin(a), q, a }
  end
  return out
end
M.vogel = vogel

-- the disc of florets on a paler ground, painted in four tones from the
-- center out; `gone` (optional) leaves some out. The spirals show in the gaps.
local function disc(N, R, spin, t_in, t_out, gone, size)
  local fl = vogel(N, R, spin)
  local c = R / sqrt(N) * (size or 0.62)
  for band = 0, 3 do
    for i, p in ipairs(fl) do
      if not (gone and gone[i]) and floor(p[3] * 3.999) == band then seed(p[1], p[2], c * (0.8 + 0.4 * p[3]), p[4]) end
    end
    ink.fill(tone(lerp(t_in, t_out, band / 3)))
  end
  return fl, c
end
-- the spirals the eye finds in the disc (parastichies): floret i and i + step
-- are neighbors where step is a Fibonacci number, 13 and 21 inside, 21 and 34
-- farther out, winding in opposite directions
local function parastichies(fl, steps)
  for _, st in ipairs(steps) do
    local step, from = st[1], st[2]
    for j = from, from + step - 1 do
      local pts = {}
      for i = j, #fl, step do pts[#pts + 1] = { fl[i][1], fl[i][2] } end
      if #pts > 2 then ink.smooth(pts, false) end
    end
  end
end

-- The disc gone to seed: seeds on Vogel's spiral over a pale ground, a few
-- gone from the rim; drawn large, the spirals through them are traced in
-- copper. r = radius (cm).
function M.phyllotaxis(rng, r, o)
  o = o or {}
  ink.push() ink.scale(r)
  local fine = ink.unit() > 0.2 and not ghost()
  local N = fine and 150 or 70
  local R = 0.8
  local spin = rng.range(0, 2 * pi)
  local fl = vogel(N, R, spin)
  local gone = {}
  for i, p in ipairs(fl) do gone[i] = p[3] > 0.85 and rng.chance(0.3) end
  ink.circle(0, 0, R * 0.98) ink.fill(tone(0.8))
  local _, c = disc(N, R, spin, 0.03, 0.2, gone, 0.5)
  if fine and ink.unit() > 0.9 then
    parastichies(fl, { { 21, 30 }, { 34, 45 } })
    ink.stroke(ink.accent(0), 0.25, 0.85)
  end
  -- a few seeds on their way
  local side = o.side or (rng.chance(0.5) and 1 or -1)
  for _ = 1, o.drift or rng.int(2, 4) do
    local a = (90 - side * rng.range(20, 70)) * rad
    local dd = rng.range(1.0, 1.5)
    seed(dd * cos(a), dd * sin(a), c * 1.3, rng.range(0, pi))
  end
  ink.fill(tone(0.1))
  ink.pop()
end

-- A Maurer rose: the points of r = sin(nθ) at θ = 0°, d°, 2d°, ... 360·d° joined
-- by straight lines, over the rose itself in a pale wash. r = radius (cm).
local MAURER = { { 2, 39 }, { 6, 71 }, { 5, 97 }, { 4, 31 }, { 7, 19 }, { 3, 47 } }
function M.maurer(rng, r, o)
  o = o or {}
  local p = o.k or MAURER[rng.int(1, #MAURER)]
  local n, d = p[1], p[2]
  ink.push() ink.scale(r) ink.rotate(rng.range(0, 360))
  local rose = {}
  local N = nlobes(n, 1)
  local out = lobe(n, 16)
  -- the lobes of sin(nθ) are centered at θ = 90°/n + j·360°/N
  for j = 0, N - 1 do ink.push() ink.rotate(90 / n - 90 + j * 360 / N) ink.smooth(out, true) ink.pop() end
  ink.fill(tone(0.62), 0.7, true)
  if not ghost() then
    local pts = {}
    for i = 0, 360 do
      local th = i * d * rad
      local rr = sin(n * th)
      pts[#pts + 1] = { rr * cos(th), rr * sin(th) }
    end
    ink.poly(pts, false) ink.stroke(tone(0.1), 0.12, 0.45)
    local period = n % 2 == 1 and pi or 2 * pi
    for i = 0, 8 * N - 1 do
      local th = period * i / (8 * N)
      local rr = sin(n * th)
      rose[#rose + 1] = { rr * cos(th), rr * sin(th) }
    end
    ink.smooth(rose, true) ink.stroke(tone(0.08), 0.3, 0.8)
    ink.circle(0, 0, 0.035) ink.fill(ink.accent(0))
  end
  ink.pop()
end

-- ---------------------------------------------------------------- the butterfly
-- Temple Fay's butterfly curve: ρ(t) = e^cos t − 2 cos 4t − sin⁵(t/12), at
-- (sin t, cos t)·ρ for t in [0, 12π]. One period without the slow term is the
-- wash of the wings, the whole curve the line over it. Head toward +y, center
-- at the origin; s = wingspan (cm). o.open narrows the wings: a wingbeat.
function M.fay(rng, s, o)
  o = o or {}
  local open = o.open or 1
  local fine = ink.unit() * s > 0.6 and not ghost()
  ink.push() ink.scale(s / 5.81) ink.translate(0, -0.66) ink.scale(open, 1)
  local t0 = o.tone or rng.range(0.3, 0.42)
  local function curve(m, T, slow)
    local pts = {}
    for i = 0, m - 1 do
      local t = T * i / m
      local rho = exp(cos(t)) - 2 * cos(4 * t) - (slow and sin(t / 12) ^ 5 or 0)
      pts[#pts + 1] = { sin(t) * rho, cos(t) * rho }
    end
    return pts
  end
  local wings = curve(96, 2 * pi)
  ink.smooth(wings, true) ink.fill(tone(t0 + 0.12), 0.85)
  ink.smooth(wings, true) ink.clip()
    flora.mottle(rng, -3, -1.8, 3, 3.2, fine and 10 or 4, 0.5, t0 - 0.2, t0 + 0.15, fine and 10 or 0)
  ink.unclip()
  if fine then ink.smooth(curve(720, 12 * pi, true), true) ink.stroke(tone(0.06), 0.2, 0.75) end
  -- the body and the antennae
  ink.push() ink.scale(1 / open, 1)
  local hb = function(v) return 0.13 * sin(pi * v ^ 0.7) end
  ink.smooth(ink.blade(function(v) return 0, -0.9 + 2.2 * v end, 10, hb, hb), true) ink.fill(tone(0.05))
  ink.circle(0, 1.4, 0.16) ink.fill(tone(0.04))
  for _, sx in ipairs({ -1, 1 }) do
    ink.moveto(sx * 0.05, 1.5) ink.curveto(sx * 0.15, 2.0, sx * 0.4, 2.4, sx * 0.6, 2.6)
    ink.stroke(tone(0.08), 0.35)
    ink.circle(sx * 0.6, 2.6, 0.06) ink.fill(tone(0.06))
  end
  ink.pop()
  ink.pop()
end

-- ---------------------------------------------------------------- 3-D
-- yaw about y, then pitch about x (degrees); the viewer looks along -z
local function rotation(yaw, pitch)
  local ca, sa, cb, sb = cos(yaw * rad), sin(yaw * rad), cos(pitch * rad), sin(pitch * rad)
  return function(x, y, z)
    local x1, z1 = ca * x + sa * z, -sa * x + ca * z
    return x1, cb * y - sb * z1, sb * y + cb * z1
  end
end

-- ---------------------------------------------------------------- the figures
-- Each figure: pick(layout) -> its parameters (chosen once, outside the drawing,
-- so the animation can replay the drawing), draw(rng, R, p) inside a disc of
-- radius R (cm) around the origin, caption(p) -> TeX for the label under it.
local FIG = {}

-- Maurer rose (theme-math.lua draws it)
local MAURER = { { 2, 39 }, { 6, 71 }, { 5, 97 }, { 4, 31 }, { 7, 19 }, { 3, 47 } }
FIG.maurer = {
  w = 2, max = 2, r = { 0.7, 1.3 },
  pick = function(L) return MAURER[L.int(1, #MAURER)] end,
  draw = function(rng, R, p) M.maurer(rng, R, { k = p }) end,
  caption = function(p) return string.format("$r=\\sin %d\\theta$, $d=%d^\\circ$", p[1], p[2]) end,
}

-- a hypotrochoid, and how it is made: the fixed circle (dashed), the rolling
-- circle at one moment, and the arm from its center to the pen (copper)
local HYPO = { { 5, 3, 0.8 }, { 7, 4, 0.9 }, { 8, 3, 0.75 }, { 5, 2, 0.9 }, { 7, 3, 0.7 }, { 9, 4, 0.85 } }
FIG.hypotrochoid = {
  w = 2, max = 2, r = { 0.7, 1.3 },
  pick = function(L) local p = HYPO[L.int(1, #HYPO)] return { p[1], p[2], p[3], L.range(0, 360) } end,
  draw = function(rng, R, p)
    local Rf, q, d = p[1], p[2], p[3] * p[2]
    local k, A = (Rf - q) / q, Rf - q
    local sc = R / Rf
    local laps = q / gcd(Rf, q)
    ink.push() ink.scale(sc) ink.rotate(p[4])
    ink.circle(0, 0, Rf) ink.stroke(tone(0.45), 0.2, 0.8, false, "[1.2 1.6] 0")
    local pts, m = {}, floor(60 * laps)
    for i = 0, m - 1 do
      local t = 2 * pi * laps * i / m
      pts[#pts + 1] = { A * cos(t) + d * cos(k * t), A * sin(t) - d * sin(k * t) }
    end
    ink.smooth(pts, true) ink.fill(tone(0.85), 0.5, true)
    ink.smooth(pts, true) ink.stroke(ink_line(), 0.32, 0.9)
    local t = 0.6
    local cx, cy = A * cos(t), A * sin(t)
    local px, py = cx + d * cos(k * t), cy - d * sin(k * t)
    ink.circle(cx, cy, q) ink.stroke(tone(0.35), 0.25, 0.85)
    ink.moveto(cx, cy) ink.lineto(px, py) ink.stroke(ink.accent(0), 0.3)
    ink.circle(cx, cy, 0.06 * Rf / 5) ink.fill(tone(0.1))
    ink.circle(px, py, 0.09 * Rf / 5) ink.fill(ink.accent(0))
    ink.pop()
  end,
  caption = function(p) return string.format("hypotrochoid $%d:%d$", p[1], p[2]) end,
}

local LISSA = { { 3, 2 }, { 5, 4 }, { 3, 4 }, { 5, 6 }, { 1, 2 }, { 5, 2 }, { 4, 3 } }
FIG.lissajous = {
  w = 2, max = 2, r = { 0.6, 1.1 },
  pick = function(L) local p = LISSA[L.int(1, #LISSA)] return { p[1], p[2], L.chance(0.5) } end,
  draw = function(rng, R, p)
    local a, b = p[1], p[2]
    local h = R * 0.7
    local delta = p[4] or (p[3] and pi / 2 / b or pi / 4 / b)
    ink.poly({ { -h, -h }, { h, -h }, { h, h }, { -h, h } }, true) ink.stroke(tone(0.5), 0.2, 0.7)
    local pts, m = {}, 60 * max(a, b)
    for i = 0, m - 1 do
      local t = 2 * pi * i / m
      pts[#pts + 1] = { h * sin(a * t + delta), h * sin(b * t) }
    end
    ink.smooth(pts, true) ink.stroke(ink_line(), 0.4, 0.9)
  end,
  caption = function(p) return string.format("$x=\\sin %st,\\ y=\\sin %st$", p[1] == 1 and "" or p[1], p[2]) end,
}

-- the Platonic solids: vertices, then faces found as the planes through three
-- vertices with all the others on one side
local function signs(p, out)
  for _, sx in ipairs(p[1] == 0 and { 0 } or { 1, -1 }) do
    for _, sy in ipairs(p[2] == 0 and { 0 } or { 1, -1 }) do
      for _, sz in ipairs(p[3] == 0 and { 0 } or { 1, -1 }) do
        out[#out + 1] = { sx == 0 and 0 or sx * p[1], sy == 0 and 0 or sy * p[2], sz == 0 and 0 or sz * p[3] }
      end
    end
  end
end
local function cyclic(list)
  local out = {}
  for _, p in ipairs(list) do signs(p, out) signs({ p[3], p[1], p[2] }, out) signs({ p[2], p[3], p[1] }, out) end
  return out
end
local SOLIDS = {
  { "tetrahedron", "3,3", { { 1, 1, 1 }, { 1, -1, -1 }, { -1, 1, -1 }, { -1, -1, 1 } } },
  { "cube", "4,3", (function() local o = {} signs({ 1, 1, 1 }, o) return o end)() },
  { "octahedron", "3,4", cyclic({ { 1, 0, 0 } }) },
  { "dodecahedron", "5,3", (function() local o = {} signs({ 1, 1, 1 }, o) for _, p in ipairs(cyclic({ { 0, 1 / PHI, PHI } })) do o[#o + 1] = p end return o end)() },
  { "icosahedron", "3,5", cyclic({ { 0, 1, PHI } }) },
}
-- the faces of the convex hull of points v around the origin, found as the
-- planes through a point and two of its nearest neighbors (for the uniform solids
-- these are its edges) with every other point on one side; then the edges
local function hull_of(v)
  local n, faces, seen = #v, {}, {}
  local function d2(a, b) return (a[1] - b[1]) ^ 2 + (a[2] - b[2]) ^ 2 + (a[3] - b[3]) ^ 2 end
  for a = 1, n do
    local near, dmin = {}, math.huge
    for b = 1, n do if b ~= a then dmin = min(dmin, d2(v[a], v[b])) end end
    for b = 1, n do if b ~= a and d2(v[a], v[b]) < dmin * 1.05 then near[#near + 1] = b end end
    for bi = 1, #near - 1 do for ci = bi + 1, #near do
      local A, B, C = v[a], v[near[bi]], v[near[ci]]
      local ux, uy, uz = B[1] - A[1], B[2] - A[2], B[3] - A[3]
      local wx, wy, wz = C[1] - A[1], C[2] - A[2], C[3] - A[3]
      local nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
      local L = sqrt(nx * nx + ny * ny + nz * nz)
      if L > 1e-9 then
        nx, ny, nz = nx / L, ny / L, nz / L
        local d = nx * A[1] + ny * A[2] + nz * A[3]
        if d < 0 then nx, ny, nz, d = -nx, -ny, -nz, -d end
        local ok = d > 1e-6
        for m = 1, n do if ok and nx * v[m][1] + ny * v[m][2] + nz * v[m][3] > d + 1e-6 then ok = false end end
        local key = floor(nx * 1000 + 0.5) .. " " .. floor(ny * 1000 + 0.5) .. " " .. floor(nz * 1000 + 0.5)
        if ok and not seen[key] then
          seen[key] = true
          local f, cx, cy, cz = {}, 0, 0, 0
          for m = 1, n do
            if abs(nx * v[m][1] + ny * v[m][2] + nz * v[m][3] - d) < 1e-6 then
              f[#f + 1] = m cx, cy, cz = cx + v[m][1], cy + v[m][2], cz + v[m][3]
            end
          end
          cx, cy, cz = cx / #f, cy / #f, cz / #f
          -- around the face's center, counterclockwise seen from outside
          local e = v[f[1]]
          local e1x, e1y, e1z = e[1] - cx, e[2] - cy, e[3] - cz
          local e2x, e2y, e2z = ny * e1z - nz * e1y, nz * e1x - nx * e1z, nx * e1y - ny * e1x
          local ang = {}
          for _, m in ipairs(f) do
            local px, py, pz = v[m][1] - cx, v[m][2] - cy, v[m][3] - cz
            ang[m] = math.atan(px * e2x + py * e2y + pz * e2z, px * e1x + py * e1y + pz * e1z)
          end
          table.sort(f, function(p, q) return ang[p] < ang[q] end)
          faces[#faces + 1] = { n = { nx, ny, nz }, v = f }
        end
      end
    end end
  end
  local edges, idx = {}, {}
  for fi, f in ipairs(faces) do
    for j = 1, #f.v do
      local a, b = f.v[j], f.v[j % #f.v + 1]
      local key = min(a, b) * 1000 + max(a, b)
      if idx[key] then edges[idx[key]].f[2] = fi
      else edges[#edges + 1] = { a = a, b = b, f = { fi } } idx[key] = #edges end
    end
  end
  local r = 0
  for _, p in ipairs(v) do r = max(r, sqrt(p[1] ^ 2 + p[2] ^ 2 + p[3] ^ 2)) end
  return { faces = faces, edges = edges, radius = r }
end
local hulls = {}
local function hull(i)
  if not hulls[i] then hulls[i] = hull_of(SOLIDS[i][3]) end
  return hulls[i]
end
-- a solid truncated at its vertices: the points a fraction s along every edge
-- from each end (s = 1/2: rectified, the edges' midpoints)
function M.truncate(v, s)
  local h, out, seen = hull_of(v), {}, {}
  local function add(p)
    local key = floor(p[1] * 1e4 + 0.5) .. " " .. floor(p[2] * 1e4 + 0.5) .. " " .. floor(p[3] * 1e4 + 0.5)
    if not seen[key] then seen[key] = true out[#out + 1] = p end
  end
  for _, e in ipairs(h.edges) do
    local a, b = v[e.a], v[e.b]
    add({ a[1] + s * (b[1] - a[1]), a[2] + s * (b[2] - a[2]), a[3] + s * (b[3] - a[3]) })
    add({ b[1] + s * (a[1] - b[1]), b[2] + s * (a[2] - b[2]), b[3] + s * (a[3] - b[3]) })
  end
  return out
end
M.hull_of = hull_of
M.hull = hull

-- a convex solid (points v, hull h) in wireframe: k cm per unit, seen from yaw, pitch
function M.solid(v, h, k, yaw, pitch)
    local rot = rotation(yaw, pitch)
    local P, front = {}, {}
    for i, q in ipairs(v) do local x, y, z = rot(q[1], q[2], q[3]) P[i] = { x * k, y * k, z } end
    local lx, ly, lz = -0.45, 0.6, 0.66                  -- light from the upper left, toward the viewer
    local lit = {}
    for fi, f in ipairs(h.faces) do
      local nx, ny, nz = rot(f.n[1], f.n[2], f.n[3])
      front[fi] = nz > 1e-6
      lit[fi] = max(0, nx * lx + ny * ly + nz * lz)
    end
    -- hidden edges dashed, then the visible faces washed over them, then the visible edges
    for _, e in ipairs(h.edges) do
      if not (front[e.f[1]] or front[e.f[2]]) then ink.moveto(P[e.a][1], P[e.a][2]) ink.lineto(P[e.b][1], P[e.b][2]) end
    end
    ink.stroke(tone(0.35), 0.25, 0.75, false, "[1.5 1.5] 0")
    for fi, f in ipairs(h.faces) do
      if front[fi] then
        local pts = {}
        for _, m in ipairs(f.v) do pts[#pts + 1] = { P[m][1], P[m][2] } end
        ink.poly(pts, true) ink.fill(tone(lerp(0.66, 0.93, lit[fi])), 0.75, true)
      end
    end
    for _, e in ipairs(h.edges) do
      if front[e.f[1]] or front[e.f[2]] then ink.moveto(P[e.a][1], P[e.a][2]) ink.lineto(P[e.b][1], P[e.b][2]) end
    end
    ink.stroke(ink_line(), 0.45)
end
FIG.polyhedron = {
  w = 3, max = 2, r = { 0.55, 1.15 },
  pick = function(L) return { L.int(1, #SOLIDS), L.range(0, 360), L.range(14, 32) } end,
  draw = function(rng, R, p)
    local h = hull(p[1])
    M.solid(SOLIDS[p[1]][3], h, R * 0.95 / h.radius, p[2], p[3])
  end,
  caption = function(p) return string.format("%s $\\{%s\\}$", SOLIDS[p[1]][1], SOLIDS[p[1]][2]) end,
}

-- knots: a closed curve in space, drawn as a tube; where it crosses itself the
-- strand on top is drawn again over a gap of paper
local function torus(p, q) return function(t) local r = 2 + cos(q * t) return r * cos(p * t), r * sin(p * t), sin(q * t) end end
local KNOTS = {
  { "trefoil", "3_1", torus(2, 3) },
  { "figure-eight knot", "4_1", function(t) local r = 2 + cos(2 * t) return r * cos(3 * t), r * sin(3 * t), sin(4 * t) end },
  { "cinquefoil", "5_1", torus(2, 5) },
  { "torus knot", "T_{3,4}", torus(3, 4) },
  { "torus knot", "7_1", torus(2, 7) },
  { "torus knot", "9_1", torus(2, 9) },
}
local function crossings(P)
  local n, out = #P, {}
  for i = 1, n do
    local a, b = P[i], P[i % n + 1]
    for j = i + 2, n do
      if not (i == 1 and j == n) then
        local c, d = P[j], P[j % n + 1]
        local rx, ry, sx, sy = b[1] - a[1], b[2] - a[2], d[1] - c[1], d[2] - c[2]
        local den = rx * sy - ry * sx
        if abs(den) > 1e-12 then
          local t = ((c[1] - a[1]) * sy - (c[2] - a[2]) * sx) / den
          local u = ((c[1] - a[1]) * ry - (c[2] - a[2]) * rx) / den
          if t >= 0 and t < 1 and u >= 0 and u < 1 then
            local za, zc = lerp(a[3], b[3], t), lerp(c[3], d[3], u)
            out[#out + 1] = za > zc and i or j               -- the segment on top
          end
        end
      end
    end
  end
  return out
end
FIG.knot = {
  w = 3, max = 2, r = { 0.55, 1.05 },
  pick = function(L) return { L.int(1, #KNOTS), L.range(0, 360) } end,
  draw = function(rng, R, p)
    local K = KNOTS[p[1]]
    local n, P = 240, {}
    local c, s = cos(p[2] * rad), sin(p[2] * rad)
    for i = 1, n do
      local x, y, z = K[3](2 * pi * (i - 1) / n)
      P[i] = { (x * c - y * s) * R / 3.05, (x * s + y * c) * R / 3.05, z }
    end
    local W = 1.5
    local function piece(i, a, b)
      local pts = {}
      for j = i + a, i + b do pts[#pts + 1] = P[(j - 1) % n + 1] end
      return pts
    end
    local function tube(pts, closed)
      ink.smooth(pts, closed) ink.stroke(ink_line(), W)
      ink.smooth(pts, closed) ink.stroke(tone(0.55), 0.45)
    end
    tube(P, true)
    for _, i in ipairs(crossings(P)) do
      ink.smooth(piece(i, -2, 3), false) ink.stroke(ink.paper, W + 2.4)
      tube(piece(i, -4, 5), false)
    end
  end,
  caption = function(p) return string.format("%s $%s$", KNOTS[p[1]][1], KNOTS[p[1]][2]) end,
}

-- Apollonian gasket: from four mutually tangent circles (curvatures -1, 2, 2, 3),
-- each new circle is the other solution of Descartes' theorem for three of them:
-- k' = 2(k1+k2+k3) - k4, and the same for k·z with z the center as a complex number
FIG.gasket = {
  w = 1, max = 1, r = { 0.95, 1.45 },
  pick = function(L) return { L.range(0, 360) } end,
  draw = function(rng, R, p)
    local kmax = min(70, 0.9 * R / 0.02)                 -- nothing smaller than 0.2 mm
    local circles = {}
    local function add(c) circles[#circles + 1] = c end
    local function gen(a, b, c, d)
      local k = 2 * (a.k + b.k + c.k) - d.k
      if k > kmax then return end
      local x = (2 * (a.k * a.x + b.k * b.x + c.k * c.x) - d.k * d.x) / k
      local y = (2 * (a.k * a.y + b.k * b.y + c.k * c.y) - d.k * d.y) / k
      local e = { k = k, x = x, y = y }
      add(e)
      gen(a, b, e, c) gen(a, c, e, b) gen(b, c, e, a)
    end
    local O = { k = -1, x = 0, y = 0 }
    local A, B, C = { k = 2, x = -0.5, y = 0 }, { k = 2, x = 0.5, y = 0 }, { k = 3, x = 0, y = 2 / 3 }
    add(A) add(B) add(C)
    gen(O, A, B, C) gen(O, A, C, B) gen(O, B, C, A) gen(A, B, C, O)
    ink.push() ink.scale(R * 0.97) ink.rotate(p[1])
    -- washes by size, the large circles palest
    for band, lim in ipairs({ 2.5, 6, 15, math.huge }) do
      local any = false
      for _, c in ipairs(circles) do
        local lo = band == 1 and 0 or ({ 2.5, 6, 15 })[band - 1]
        if c.k > lo and c.k <= lim then ink.circle(c.x, c.y, 1 / c.k) any = true end
      end
      if any then ink.fill(tone(({ 0.9, 0.8, 0.68, 0.55 })[band])) end
    end
    for _, c in ipairs(circles) do ink.circle(c.x, c.y, 1 / c.k) end
    ink.stroke(tone(0.12), 0.18, 0.85)
    ink.circle(0, 0, 1) ink.stroke(ink_line(), 0.4)
    ink.pop()
  end,
  caption = function() return "Apollonian gasket" end,
}

-- Koch snowflake: each edge replaced by four, three times or four; the triangle
-- it grew from dashed in copper
FIG.koch = {
  w = 1.5, max = 1, r = { 0.7, 1.25 },
  pick = function(L) return { L.range(0, 120) } end,
  draw = function(rng, R, p)
    local tri = {}
    for k = 0, 2 do local a = (90 - 120 * k + p[1]) * rad tri[#tri + 1] = { cos(a), sin(a) } end
    local pts = tri
    for _ = 1, p[2] or (R > 0.9 and 4 or 3) do
      local nxt = {}
      for i = 1, #pts do
        local a, b = pts[i], pts[i % #pts + 1]
        local dx, dy = (b[1] - a[1]) / 3, (b[2] - a[2]) / 3
        local c60, s60 = 0.5, sqrt(3) / 2
        nxt[#nxt + 1] = a
        nxt[#nxt + 1] = { a[1] + dx, a[2] + dy }
        nxt[#nxt + 1] = { a[1] + dx + dx * c60 - dy * s60, a[2] + dy + dx * s60 + dy * c60 }
        nxt[#nxt + 1] = { a[1] + 2 * dx, a[2] + 2 * dy }
      end
      pts = nxt
    end
    ink.push() ink.scale(R * 0.97)
    ink.poly(pts, true) ink.fill(tone(0.84), 0.8, true)
    ink.poly(tri, true) ink.stroke(ink.accent(0), 0.25, 0.85, false, "[1.5 1.5] 0")
    ink.poly(pts, true) ink.stroke(ink_line(), 0.32)
    ink.pop()
  end,
  caption = function() return "Koch snowflake, $\\dim = \\log_3 4$" end,
}

-- Hilbert curve: cell d of the n×n grid by the usual bit twiddling
local function hilbert(order)
  local n, pts = 1 << order, {}
  for d = 0, n * n - 1 do
    local x, y, t, s = 0, 0, d, 1
    while s < n do
      local rx = (t // 2) & 1
      local ry = (t ~ rx) & 1
      if ry == 0 then
        if rx == 1 then x, y = s - 1 - x, s - 1 - y end
        x, y = y, x
      end
      x, y = x + s * rx, y + s * ry
      t = t // 4
      s = s * 2
    end
    pts[#pts + 1] = { x, y }
  end
  return pts, n
end
FIG.hilbert = {
  w = 1.5, max = 1, r = { 0.6, 1.1 },
  pick = function(L) return { L.int(0, 3) } end,
  draw = function(rng, R, p)
    local order = p[2] or (R > 0.85 and 4 or 3)
    local pts, n = hilbert(order)
    local h = R * 0.7
    local out = {}
    for i, q in ipairs(pts) do out[i] = { -h + (q[1] + 0.5) / n * 2 * h, -h + (q[2] + 0.5) / n * 2 * h } end
    ink.push() ink.rotate(90 * p[1])
    ink.poly({ { -h, -h }, { h, -h }, { h, h }, { -h, h } }, true) ink.fill(tone(0.9), 0.7, true)
    ink.poly({ { -h, -h }, { h, -h }, { h, h }, { -h, h } }, true) ink.stroke(tone(0.45), 0.2, 0.7)
    ink.poly(out, false) ink.stroke(ink_line(), 0.4)
    ink.circle(out[1][1], out[1][2], 0.025) ink.circle(out[#out][1], out[#out][2], 0.025) ink.fill(ink.accent(0))
    ink.pop()
  end,
  caption = function(p) return "Hilbert curve" end,
}

-- chords k -> m·k mod n on a circle; they envelop an epicycloid with m - 1 cusps
FIG.chords = {
  w = 1.5, max = 1, r = { 0.75, 1.3 },
  pick = function(L) return { L.int(2, 4), L.pick({ 100, 120, 150 }), L.range(0, 360) } end,
  draw = function(rng, R, p)
    local m, n = p[1], p[2]
    local r = R * 0.95
    ink.push() ink.rotate(p[3])
    for k = 0, n - 1 do
      local a, b = 2 * pi * k / n, 2 * pi * (m * k % n) / n
      if k ~= m * k % n then ink.moveto(r * cos(a), r * sin(a)) ink.lineto(r * cos(b), r * sin(b)) end
    end
    ink.stroke(tone(0.2), 0.15, 0.6)
    local env = {}
    for i = 0, 179 do
      local t = 2 * pi * i / 180
      env[#env + 1] = { r * (m * cos(t) + cos(m * t)) / (m + 1), r * (m * sin(t) + sin(m * t)) / (m + 1) }
    end
    ink.smooth(env, true) ink.stroke(ink.accent(0), 0.35, 0.9)
    ink.circle(0, 0, r) ink.stroke(ink_line(), 0.35)
    ink.pop()
  end,
  caption = function(p) return string.format("$k\\mapsto %dk \\bmod %d$", p[1], p[2]) end,
}

-- golden rectangles: cut a square off a golden rectangle and what is left is
-- golden again; a quarter circle in each square makes the spiral
FIG.golden = {
  w = 1.5, max = 1, r = { 0.75, 1.3 },
  pick = function(L) return { L.int(0, 3), L.chance(0.5) } end,
  draw = function(rng, R, p)
    local x, y, w, h = -PHI / 2, -0.5, PHI, 1
    local squares, arc = {}, {}
    local cx, cy
    for i = 0, 13 do
      local d, s, a0 = i % 4
      if d == 0 then s = h squares[#squares + 1] = { x, y, s } cx, cy, a0 = x + s, y, 180 x, w = x + s, w - s
      elseif d == 1 then s = w squares[#squares + 1] = { x, y + h - s, s } cx, cy, a0 = x, y + h - s, 90 h = h - s
      elseif d == 2 then s = h squares[#squares + 1] = { x + w - s, y, s } cx, cy, a0 = x + w - s, y + s, 0 w = w - s
      else s = w squares[#squares + 1] = { x, y, s } cx, cy, a0 = x + s, y + s, -90 y, h = y + s, h - s end
      for j = (i == 0 and 0 or 1), 8 do
        local a = (a0 - 90 * j / 8) * rad
        arc[#arc + 1] = { cx + s * cos(a), cy + s * sin(a) }
      end
    end
    local k = R * 0.98 / sqrt(PHI * PHI + 1) * 2
    ink.push() ink.rotate(90 * p[1]) if p[2] then ink.scale(-1, 1) end ink.scale(k)
    local q = squares[1]
    ink.poly({ { q[1], q[2] }, { q[1] + q[3], q[2] }, { q[1] + q[3], q[2] + q[3] }, { q[1], q[2] + q[3] } }, true)
    ink.fill(tone(0.88), 0.7, true)
    for i = 1, 9 do
      q = squares[i]
      ink.poly({ { q[1], q[2] }, { q[1] + q[3], q[2] }, { q[1] + q[3], q[2] + q[3] }, { q[1], q[2] + q[3] } }, true)
    end
    ink.stroke(tone(0.4), 0.2, 0.75)
    ink.smooth(arc, false) ink.stroke(ink_line(), 0.45)
    ink.circle(arc[#arc][1], arc[#arc][2], 0.012 / k * 2) ink.fill(ink.accent(0))
    ink.pop()
  end,
  caption = function() return "$\\varphi = \\frac{1+\\sqrt5}{2}$" end,
}

-- a parabola x^2 = 4fy: rays parallel to its axis reflect into the focus
FIG.parabola = {
  w = 1, max = 1, r = { 0.7, 1.15 },
  pick = function(L) return { L.range(0.2, 0.3) } end,
  draw = function(rng, R, p)
    local f = p[1]
    local X = 0.9
    ink.push() ink.scale(R) ink.translate(0, -0.35)
    ink.moveto(-X, -f) ink.lineto(X, -f) ink.stroke(tone(0.35), 0.25, 0.8, false, "[2 1.5] 0")
    ink.moveto(0, -f - 0.05) ink.lineto(0, 0.95) ink.stroke(tone(0.45), 0.18, 0.6, false, "[0.6 1.4] 0")
    for _, x in ipairs({ -0.75, -0.5, -0.25, 0.25, 0.5, 0.75 }) do
      local y = x * x / (4 * f)
      if y < 0.95 then ink.moveto(x, 0.95) ink.lineto(x, y) ink.lineto(0, f) end
    end
    ink.stroke(ink.accent(0), 0.22, 0.8)
    local pts = {}
    for i = 0, 40 do
      local x = -X + 2 * X * i / 40
      local y = x * x / (4 * f)
      if y <= 1.0 then pts[#pts + 1] = { x, y } end
    end
    ink.smooth(pts, false) ink.stroke(ink_line(), 0.45)
    ink.circle(0, f, 0.03) ink.fill(ink.accent(-0.1))
    ink.pop()
  end,
  caption = function(p) return "$x^2 = 4fy$" end,
}

-- the Petersen graph, its vertices properly colored with three colors
local PETERSEN = {}
do
  for i = 0, 4 do
    PETERSEN[#PETERSEN + 1] = { i, (i + 1) % 5 }          -- the outer cycle
    PETERSEN[#PETERSEN + 1] = { i, i + 5 }                -- the spokes
    PETERSEN[#PETERSEN + 1] = { i + 5, (i + 2) % 5 + 5 }  -- the inner star
  end
end
local function three_colors()
  local col, adj = {}, {}
  for v = 0, 9 do adj[v] = {} end
  for _, e in ipairs(PETERSEN) do adj[e[1]][#adj[e[1]] + 1] = e[2] adj[e[2]][#adj[e[2]] + 1] = e[1] end
  local function try(v)
    if v > 9 then return true end
    for c = 1, 3 do
      local ok = true
      for _, u in ipairs(adj[v]) do if col[u] == c then ok = false end end
      if ok then col[v] = c if try(v + 1) then return true end col[v] = nil end
    end
    return false
  end
  try(0)
  return col
end
local PCOL = three_colors()
FIG.petersen = {
  w = 1.5, max = 1, r = { 0.6, 1.05 },
  pick = function(L) return { L.range(-8, 8) } end,
  draw = function(rng, R, p)
    local P = {}
    for i = 0, 4 do
      local a = (90 + 72 * i + p[1]) * rad
      P[i] = { R * 0.92 * cos(a), R * 0.92 * sin(a) }
      P[i + 5] = { R * 0.45 * cos(a), R * 0.45 * sin(a) }
    end
    for _, e in ipairs(PETERSEN) do ink.moveto(P[e[1]][1], P[e[1]][2]) ink.lineto(P[e[2]][1], P[e[2]][2]) end
    ink.stroke(ink_line(), 0.4)
    local colors = { tone(0.08), tone(0.5), ink.accent(0) }
    for c = 1, 3 do
      for v = 0, 9 do if PCOL[v] == c then ink.circle(P[v][1], P[v][2], 0.055) end end
      ink.fill(colors[c])
    end
    for v = 0, 9 do ink.circle(P[v][1], P[v][2], 0.055) end
    ink.stroke(ink_line(), 0.3)
  end,
  caption = function() return "Petersen graph, $\\chi = 3$" end,
}

FIG.vogel = {
  w = 1, max = 1, r = { 0.6, 1.1 },
  pick = function(L) return {} end,
  draw = function(rng, R, p) M.phyllotaxis(rng, R / 0.8, { drift = 0 }) end,
  caption = function() return "$r_n = c\\sqrt n$, $\\theta_n = 137.5^\\circ n$" end,
}

FIG.fay = {
  w = 0.7, max = 1, r = { 0.7, 1.2 },
  pick = function(L) return {} end,
  draw = function(rng, R, p) M.fay(rng, 1.5 * R) end,
  caption = function() return "Fay's butterfly curve" end,
}

-- a fixed order, for the weighted choice (pairs() is not)
M.figures, M.solids, M.rotation, M.cyclic = FIG, SOLIDS, rotation, cyclic
M.figure_order = { "polyhedron", "knot", "maurer", "hypotrochoid", "lissajous", "gasket", "koch", "hilbert",
  "chords", "golden", "parabola", "petersen", "vogel", "fay" }

-- ---------------------------------------------------------------- the fleuron
-- for the header: a copper circle with an inscribed triangle, its tangent running
-- out into the head rule. Origin where the ivy leaf's notch would be; returns the
-- end of the line in page cm, as flora.hedera does.
function M.compass(rng, s, o)
  local c = (o and o.color) or ink.accent(0)
  ink.push() ink.scale(s)
  local r, cy = 0.55, 0.0
  ink.circle(0, cy, r) ink.stroke(c, 0.4)
  local tri = {}
  for k = 0, 2 do local a = (90 + 120 * k) * rad tri[#tri + 1] = { r * cos(a), cy + r * sin(a) } end
  ink.poly(tri, true) ink.stroke(c, 0.3, 0.9)
  ink.circle(0, cy, 0.07) ink.fill(c)
  ink.moveto(0, cy + r) ink.lineto(2.0, cy + r) ink.stroke(c, 0.4)
  local rx, ry = ink.to_page(2.0, cy + r)
  ink.pop()
  return rx, ry
end

-- rough width of a caption in cm: the letters that show, at 6.5 pt
function M.caption_width(t)
  t = t:gsub("\\[a-zA-Z]+", "x"):gsub("[{}$^_\\]", "")
  return #t * 0.115
end

-- ---------------------------------------------------------------- the families
-- values: the steps; label(v): TeX for one step; title(p): TeX for the family;
-- pick(layout) -> what the family's figures share (an angle, a ratio); draw(rng, R, v, p)
local FAM = {}
M.families = FAM

FAM.rose = {
  values = { { 1, 1 }, { 3, 2 }, { 2, 1 }, { 5, 2 }, { 3, 1 }, { 7, 2 }, { 4, 1 } },
  pick = function(L) return { L.range(0, 360) } end,
  title = function() return "$r=\\cos k\\theta$" end,
  label = function(v) return v[2] == 1 and string.format("$k=%d$", v[1]) or string.format("$k=\\frac{%d}{%d}$", v[1], v[2]) end,
  draw = function(rng, R, v, p)
    local n, d = v[1], v[2]
    local k = n / d
    local period = (n * d) % 2 == 1 and pi * d or 2 * pi * d
    local pts, m = {}, 48 * max(n, 2)
    for i = 0, m - 1 do
      local t = period * i / m
      local r = R * 0.95 * cos(k * t)
      pts[#pts + 1] = { r * cos(t + p[1] * rad), r * sin(t + p[1] * rad) }
    end
    ink.smooth(pts, true) ink.fill(tone(0.82), 0.75, true)
    ink.smooth(pts, true) ink.stroke(tone(0.08), 0.4)
    ink.circle(0, 0, 0.025) ink.fill(ink.accent(0))
  end,
}

FAM.koch = {
  values = { 0, 1, 2, 3, 4 },
  pick = function(L) return { L.range(0, 120) } end,
  title = function() return "Koch snowflake" end,
  label = function(v) return string.format("$n=%d$", v) end,
  draw = function(rng, R, v, p) FIG.koch.draw(rng, R, { p[1], v }) end,
}

FAM.hilbert = {
  values = { 1, 2, 3, 4 },
  pick = function(L) return { L.int(0, 3) } end,
  title = function() return "Hilbert curves" end,
  label = function(v) return string.format("$n=%d$", v) end,
  draw = function(rng, R, v, p) FIG.hilbert.draw(rng, R, { p[1], v }) end,
}

local DELTA = { "0", "\\frac{\\pi}{8}", "\\frac{\\pi}{4}", "\\frac{3\\pi}{8}", "\\frac{\\pi}{2}" }
FAM.lissajous = {
  values = { 0, 1, 2, 3, 4 },
  pick = function(L) local r = ({ { 3, 2 }, { 1, 2 }, { 5, 4 }, { 3, 4 } })[L.int(1, 4)] return r end,
  title = function(p) return string.format("$x=\\sin(%st+\\delta)$, $y=\\sin %dt$", p[1] == 1 and "" or p[1], p[2]) end,
  label = function(v) return "$\\delta=" .. DELTA[v + 1] .. "$" end,
  draw = function(rng, R, v, p) FIG.lissajous.draw(rng, R, { p[1], p[2], false, v * pi / 8 }) end,
}

-- truncation: points a fraction s along every edge from each end; s = 1/2 is the
-- rectified solid, which the dual reaches from the other side
local CUBE, OCTA = M.solids[2][3], M.cyclic({ { 2, 0, 0 } })
local DODECA, ICOSA = M.solids[4][3], M.solids[5][3]
local shapes = {}
local function shape(v, s, key)
  if not shapes[key] then
    local pts = s > 0 and M.truncate(v, s) or v
    shapes[key] = { v = pts, h = M.hull_of(pts) }
  end
  return shapes[key]
end
local function truncation(a, b, sa, ta, tb)
  return {
    values = { { a, 0, "\\{" .. ta .. "\\}" }, { a, sa, "t\\{" .. ta .. "\\}" }, { a, 0.5, "r\\{" .. ta .. "\\}" },
      { b, 1 / 3, "t\\{" .. tb .. "\\}" }, { b, 0, "\\{" .. tb .. "\\}" } },
    pick = function(L) return { L.range(0, 360), L.range(14, 30) } end,
    label = function(v) return "$" .. v[3] .. "$" end,
    draw = function(rng, R, v, p)
      local sh = shape(v[1], v[2], v[3])
      M.solid(sh.v, sh.h, R * 0.95 / sh.h.radius, p[1], p[2])
    end,
  }
end
FAM.cube = truncation(CUBE, OCTA, 1 / (2 + sqrt(2)), "4,3", "3,4")
FAM.cube.title = function() return "from the cube to its dual" end
FAM.dodeca = truncation(DODECA, ICOSA, 1 / (2 + PHI), "5,3", "3,5")
FAM.dodeca.title = function() return "from the dodecahedron to its dual" end

FAM.knots = {
  values = { { 3, 1 }, { 5, 3 }, { 7, 5 }, { 9, 6 } },              -- T(2,q) and its place in plate's list
  pick = function(L) return { L.range(0, 360) } end,
  title = function() return "torus knots" end,
  label = function(v) return string.format("$T_{2,%d}$", v[1]) end,
  draw = function(rng, R, v, p) FIG.knot.draw(rng, R, { v[2], p[1] }) end,
}

FAM.chords = {
  values = { 2, 3, 4, 5, 6 },
  pick = function(L) return { L.pick({ 100, 120, 150 }), L.range(0, 360) } end,
  title = function(p) return string.format("$k\\mapsto mk \\bmod %d$", p[1]) end,
  label = function(v) return string.format("$m=%d$", v) end,
  draw = function(rng, R, v, p) FIG.chords.draw(rng, R, { v, p[1], p[2] }) end,
}

FAM.hypotrochoid = {
  values = { 0.25, 0.5, 0.75, 1.0, 1.25 },
  pick = function(L) local r = ({ { 5, 3 }, { 7, 4 }, { 5, 2 }, { 8, 3 } })[L.int(1, 4)] return { r[1], r[2], L.range(0, 360) } end,
  title = function(p) return string.format("hypotrochoids $%d:%d$", p[1], p[2]) end,
  label = function(v) return string.format("$d=%sr$", ({ [0.25] = "\\frac14", [0.5] = "\\frac12", [0.75] = "\\frac34", [1.0] = "", [1.25] = "\\frac54" })[v]) end,
  draw = function(rng, R, v, p) FIG.hypotrochoid.draw(rng, R, { p[1], p[2], v, p[3] }) end,
}

FAM.vogel = {
  values = { 137.0, 137.3, 137.508, 137.7, 138.0 },
  pick = function(L) return { L.range(0, 360) } end,
  title = function() return "Vogel's disc: floret $n$ at $n\\alpha$" end,
  label = function(v) return v == 137.508 and "$\\alpha=137.5^\\circ$" or string.format("$%.1f^\\circ$", v) end,
  draw = function(rng, R, v, p)
    local N = 140
    local golden = v == 137.508
    for i = 1, N do
      local a = (p[1] + i * v) * rad
      local r = R * 0.95 * sqrt((i - 0.5) / N)
      ink.circle(r * cos(a), r * sin(a), R * 0.035 * (0.6 + 0.6 * sqrt(i / N)))
    end
    ink.fill(golden and tone(0.05) or tone(0.2))
    if golden then ink.circle(0, 0, R * 0.04) ink.fill(ink.accent(0)) end
  end,
}

FAM.archimedes = {
  values = { 3, 4, 6, 8, 12, 24 },
  pick = function(L) return { L.range(0, 360) } end,
  title = function() return "Archimedes: $n\\sin\\frac{\\pi}{n}\\to\\pi$" end,
  label = function(v) return string.format("$n=%d$", v) end,
  draw = function(rng, R, v, p)
    local r = R * 0.95 * cos(pi / v)                     -- the outer polygon fits the disc
    local inner, outer = {}, {}
    for i = 0, v - 1 do
      local a = p[1] * rad + 2 * pi * i / v
      inner[#inner + 1] = { r * cos(a), r * sin(a) }
      outer[#outer + 1] = { r / cos(pi / v) * cos(a + pi / v), r / cos(pi / v) * sin(a + pi / v) }
    end
    ink.poly(outer, true) ink.fill(tone(0.88), 0.7, true)
    ink.poly(inner, true) ink.fill(tone(0.74), 0.7, true)
    ink.circle(0, 0, r) ink.stroke(ink.accent(0), 0.3)
    ink.poly(outer, true) ink.stroke(tone(0.3), 0.25)
    ink.poly(inner, true) ink.stroke(tone(0.08), 0.4)
  end,
}

FAM.superellipse = {
  values = { 0.5, 1, 1.5, 2, 3, 6 },
  pick = function(L) return { L.range(0, 45) } end,
  title = function() return "$|x|^n+|y|^n=1$" end,
  label = function(v) return v == 0.5 and "$n=\\frac12$" or v == 1.5 and "$n=\\frac32$" or string.format("$n=%d$", v) end,
  draw = function(rng, R, v, p)
    local pts, e = {}, 2 / v
    local s = R * 0.95 / (v >= 2 and 2 ^ (0.5 - 1 / v) or 1)   -- the corners of the squarer ones inside the disc
    for i = 0, 95 do
      local t = 2 * pi * i / 96
      local c, sn = cos(t), sin(t)
      local x = (c < 0 and -1 or 1) * abs(c) ^ e
      local y = (sn < 0 and -1 or 1) * abs(sn) ^ e
      local a = p[1] * rad
      pts[#pts + 1] = { s * (x * cos(a) - y * sin(a)), s * (x * sin(a) + y * cos(a)) }
    end
    ink.poly(pts, true) ink.fill(tone(0.82), 0.75, true)
    ink.poly(pts, true) ink.stroke(tone(0.08), 0.4)
  end,
}

FAM.maurer = {
  values = { 1, 19, 29, 47, 71 },
  pick = function(L) return { L.pick({ 2, 4, 6 }) } end,
  title = function(p) return string.format("Maurer roses $r=\\sin %d\\theta$", p[1]) end,
  label = function(v) return string.format("$d=%d^\\circ$", v) end,
  draw = function(rng, R, v, p) M.maurer(rng, R, { k = { p[1], v } }) end,
}

-- a fixed order, for the weighted choice (pairs() is not)
M.family_order = { "cube", "rose", "koch", "knots", "lissajous", "vogel", "chords", "hilbert", "dodeca",
  "archimedes", "superellipse", "hypotrochoid", "maurer" }

return M
