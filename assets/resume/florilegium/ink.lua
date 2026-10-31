-- ink.lua -- the drawing core of florilegium: geometry in Lua, raw PDF out.
-- Copyright (c) 2026 Kevin Raymond. MIT License: see LICENSE or florilegium.sty.
--
-- Everything is computed here and written as PDF path operators into a literal
-- node, so TeX does no arithmetic at all. A drawing is made in a local frame
-- (centimeters) under an affine transform that maps it to the page (big points);
-- strokes are absolute widths in bp, and anything that should scale with the
-- motif (stems, veins, streaks) is drawn as a filled ribbon instead of a stroke.
--
-- Color comes from a tone ramp derived from the document color `ink`:
-- tone(0) is the darkest navy, tone(1) the palest mist, all at the hue of `ink`,
-- computed in OKLCH so the light end stays blue instead of turning gray.

local M = {}

local fmt, floor, sqrt, sin, cos, atan, pi, abs = string.format, math.floor, math.sqrt, math.sin, math.cos, math.atan, math.pi, math.abs
local concat = table.concat
local rad = pi / 180
local CM = 72 / 2.54                       -- bp per cm

-- ---------------------------------------------------------------- random
-- mulberry32 (Tommy Ettinger, 2017, public domain): small, fast, identical on
-- every platform (math.random is not)
function M.rng(seed)
  local s = floor(seed) & 0xffffffff
  local r = {}
  function r.u()
    s = (s + 0x6D2B79F5) & 0xffffffff
    local t = s
    t = ((t ~ (t >> 15)) * (t | 1)) & 0xffffffff
    t = (t ~ (t + (((t ~ (t >> 7)) * (t | 61)) & 0xffffffff))) & 0xffffffff
    return ((t ~ (t >> 14)) & 0xffffffff) / 4294967296
  end
  function r.range(a, b) return a + (b - a) * r.u() end
  function r.sym(a) return a * (2 * r.u() - 1) end
  function r.int(a, b) return a + floor((b - a + 1) * r.u()) end
  function r.chance(p) return r.u() < p end
  function r.pick(t) return t[1 + floor(#t * r.u())] end
  function r.normal() local u1 = math.max(r.u(), 1e-12) return sqrt(-2 * math.log(u1)) * cos(2 * pi * r.u()) end
  function r.fork() return M.rng(floor(r.u() * 4294967295)) end   -- an independent stream
  function r.save() return s end                                  -- replay a draw (animation)
  function r.load(v) s = v end
  return r
end

-- ---------------------------------------------------------------- noise
-- 1-D gradient noise with a seeded gradient table, smooth, roughly in [-1,1]
function M.noise1(rng)
  local g = {}
  for i = 0, 255 do g[i] = rng.sym(1) end
  return function(x)
    local i = floor(x); local f = x - i
    local a, b = g[i & 255] * f, g[(i + 1) & 255] * (f - 1)
    local u = f * f * (3 - 2 * f)
    return 2 * (a + (b - a) * u)
  end
end

-- fractal sum of 1-D noise: `oct` octaves, each double frequency, half amplitude
function M.fbm1(rng, oct)
  local ns = {}
  for k = 1, oct do ns[k] = M.noise1(rng) end
  return function(x)
    local v, a, f = 0, 1, 1
    for k = 1, oct do v = v + a * ns[k](x * f + 17 * k); a = a * 0.5; f = f * 2 end
    return v
  end
end

-- ---------------------------------------------------------------- color
local function srgb_dec(c) return c <= 0.04045 and c / 12.92 or ((c + 0.055) / 1.055) ^ 2.4 end
local function srgb_enc(c) return c <= 0.0031308 and 12.92 * c or 1.055 * c ^ (1 / 2.4) - 0.055 end
local function cbrt(x) return x < 0 and -((-x) ^ (1 / 3)) or x ^ (1 / 3) end

-- OKLCH is Oklab in polar form. Oklab and the matrices below are Björn
-- Ottosson's ("A perceptual color space for image processing", 2020, public domain).
local function rgb_to_oklch(r, g, b)
  r, g, b = srgb_dec(r), srgb_dec(g), srgb_dec(b)
  local l = cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
  local m = cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
  local s = cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
  local L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
  local A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
  local B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
  return L, sqrt(A * A + B * B), atan(B, A) / rad
end

-- OKLCH -> sRGB; nil when out of gamut
local function oklch_to_rgb(L, C, h)
  local A, B = C * cos(h * rad), C * sin(h * rad)
  local l = (L + 0.3963377774 * A + 0.2158037573 * B) ^ 3
  local m = (L - 0.1055613458 * A - 0.0638541728 * B) ^ 3
  local s = (L - 0.0894841775 * A - 1.2914855480 * B) ^ 3
  local r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
  local g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
  local b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
  if r < -1e-4 or g < -1e-4 or b < -1e-4 or r > 1.0001 or g > 1.0001 or b > 1.0001 then return nil end
  local function c(x) return srgb_enc(math.min(1, math.max(0, x))) end
  return c(r), c(g), c(b)
end

-- largest in-gamut chroma at or below C
local function oklch_clamped(L, C, h)
  local r, g, b = oklch_to_rgb(L, C, h)
  if r then return r, g, b end
  local lo, hi = 0, C
  for _ = 1, 18 do local mid = (lo + hi) / 2 if oklch_to_rgb(L, mid, h) then lo = mid else hi = mid end end
  return oklch_to_rgb(L, lo, h)
end

-- the ramp: lightness and chroma per stop; chroma scales with the chroma of
-- `ink`, the hue follows `ink` and drifts slightly violet in the darks and
-- cyan in the lights, as ultramarine does when it is thinned with water
local STOPS = {   -- t, L, C, hue drift
  { 0.00, 0.25, 0.105,  6 },
  { 0.18, 0.35, 0.150,  3 },
  { 0.38, 0.47, 0.175,  0 },
  { 0.58, 0.60, 0.145, -3 },
  { 0.80, 0.77, 0.080, -6 },
  { 1.00, 0.92, 0.030, -8 },
}
local REF_C = 0.175                        -- the chroma of the default ink at the cobalt stop
local ramp = {}                            -- 101 precomputed "r g b" strings
local hue, chroma_k = 263, 1
local lift = 0                             -- ghost mode: tone t -> t + (1-t)*lift
local pale = 0                             -- the whole margin paler (option intensity), the same way

local function build_ramp()
  for i = 0, 100 do
    local t = i / 100
    local k = 1
    while STOPS[k + 1][1] < t do k = k + 1 end
    local a, b = STOPS[k], STOPS[k + 1]
    local u = (t - a[1]) / (b[1] - a[1])
    local L = a[2] + (b[2] - a[2]) * u
    local C = (a[3] + (b[3] - a[3]) * u) * chroma_k
    local h = hue + a[4] + (b[4] - a[4]) * u
    local r, g, bb = oklch_clamped(L, C, h)
    ramp[i] = { r, g, bb }
  end
end

-- set the hue from the document color `ink` (r,g,b in 0..1)
function M.set_ink(r, g, b)
  local _, C, h = rgb_to_oklch(r, g, b)
  hue, chroma_k = h, math.max(0.15, math.min(1.3, C / REF_C))
  build_ramp()
end
M.set_ink(0x24 / 255, 0x56 / 255, 0xC4 / 255)

local accent = { 0.71, 0.40, 0.18 }
function M.set_accent(r, g, b) accent = { r, g, b } end

-- a color is a table {r,g,b}; tone(t) is a point on the ramp (ghost lift applied)
function M.tone(t)
  t = t + (1 - t) * lift
  if pale > 0 then t = t + (1 - t) * pale end
  local i = math.max(0, math.min(100, floor(t * 100 + 0.5)))
  return ramp[i]
end
local function toward_white(c, v) return { c[1] + (1 - c[1]) * v, c[2] + (1 - c[2]) * v, c[3] + (1 - c[3]) * v } end
function M.accent(k)                        -- k>0 lightens toward white, k<0 darkens
  k = k or 0
  local c
  if k >= 0 then c = toward_white(accent, k)
  else c = { accent[1] * (1 + k), accent[2] * (1 + k), accent[3] * (1 + k) } end
  if pale > 0 then c = toward_white(c, pale) end
  return c
end
-- paint fn() with a ramp at the hue of the accent instead (copper leaves in autumn)
local accent_ramp, accent_key
function M.in_accent(fn)
  local key = fmt("%.3f %.3f %.3f", accent[1], accent[2], accent[3])
  local main = ramp
  if accent_key ~= key then
    local h0, c0 = hue, chroma_k
    local _, C, h = rgb_to_oklch(accent[1], accent[2], accent[3])
    ramp, hue, chroma_k = {}, h, math.max(0.15, math.min(1.3, C / REF_C))
    build_ramp()
    accent_ramp, accent_key, hue, chroma_k = ramp, key, h0, c0
  end
  ramp = accent_ramp
  fn()
  ramp = main
end
M.white = { 1, 1, 1 }
M.paper = { 0.995, 0.993, 0.985 }
function M.set_lift(v) local old = lift lift = v return old end
function M.get_lift() return lift end
-- paint everything paler: tone t -> t + (1-t)*v, accents mixed toward white as much.
-- Only the color: the level of detail still follows the ghost's lift alone.
function M.set_pale(v) local old = pale pale = v return old end

-- ---------------------------------------------------------------- transforms
-- an affine map {a,b,c,d,e,f}: x' = a x + c y + e,  y' = b x + d y + f
local T = { CM, 0, 0, CM, 0, 0 }           -- current transform: local cm -> page bp
local stack = {}

local function mul(A, B)                   -- A then B, i.e. B(A(p))
  return { B[1] * A[1] + B[3] * A[2], B[2] * A[1] + B[4] * A[2],
           B[1] * A[3] + B[3] * A[4], B[2] * A[3] + B[4] * A[4],
           B[1] * A[5] + B[3] * A[6] + B[5], B[2] * A[5] + B[4] * A[6] + B[6] }
end
function M.set_transform(t) T = t end
-- the page: cm from the lower-left corner of the paper -> bp. With `mirror` (the
-- paper width in cm) x becomes mirror - x: a garden laid out in the left margin
-- is drawn, reflected, in the right one
function M.page_transform(mirror)
  if mirror then return { -CM, 0, 0, CM, mirror * CM, 0 } end
  return { CM, 0, 0, CM, 0, 0 }
end
function M.get_transform() return T end
function M.push() stack[#stack + 1] = T end
function M.pop() T = table.remove(stack) end
function M.translate(x, y) T = { T[1], T[2], T[3], T[4], T[1] * x + T[3] * y + T[5], T[2] * x + T[4] * y + T[6] } end
function M.rotate(deg)
  local c, s = cos(deg * rad), sin(deg * rad)
  T = { T[1] * c + T[3] * s, T[2] * c + T[4] * s, -T[1] * s + T[3] * c, -T[2] * s + T[4] * c, T[5], T[6] }
end
function M.scale(sx, sy) sy = sy or sx T = { T[1] * sx, T[2] * sx, T[3] * sy, T[4] * sy, T[5], T[6] } end
-- size of one local unit on the page, in cm (for level-of-detail decisions)
function M.unit() return sqrt(abs(T[1] * T[4] - T[2] * T[3])) / CM end
-- local point -> page cm (for layout code that needs absolute positions)
function M.to_page(x, y) return (T[1] * x + T[3] * y + T[5]) / CM, (T[2] * x + T[4] * y + T[6]) / CM end

-- ---------------------------------------------------------------- output
-- Output goes into numbered layers; flush() writes them in order as one
-- literal. ExtGState resources for opacity/blend are registered with pgf.
-- While recording (the growth animation), every piece of output also keeps
-- the tag that was current when it was painted, so a frame can later write
-- only the pieces it wants, in their original order.
local layers, cur = {}, 5
local tags, tag, recording = {}, nil, false
local function put(s)
  local b = layers[cur]
  if not b then b = {} layers[cur] = b tags[cur] = {} end
  b[#b + 1] = s
  if recording then tags[cur][#b] = tag end
end
function M.layer(n) local old = cur cur = n return old end
function M.tag(t) local old = tag tag = t return old end
function M.record(on) recording = on tag = nil end

local gs_known = {}
local function gs(op, mult)
  op = floor(op * 100 + 0.5)
  if op >= 100 and not mult then return nil end
  local name = fmt("flo%s%d", mult and "m" or "a", op)
  if not gs_known[name] then
    gs_known[name] = true
    tex.sprint(luatexbase.registernumber("catcodetable@atletter"),
      fmt("\\pgfutil@addpdfresource@extgs{/%s << /ca %.2f /CA %.2f%s >>}", name, op / 100, op / 100, mult and " /BM /Multiply" or ""))
  end
  return name
end

-- 0.1 bp (0.035 mm) is finer than any printer resolves
local function P(x, y)
  return fmt("%.1f %.1f", T[1] * x + T[3] * y + T[5], T[2] * x + T[4] * y + T[6])
end

-- path construction: polyline or smooth (Catmull-Rom as Béziers) through points {{x,y},...}
local path = {}
function M.moveto(x, y) path[#path + 1] = P(x, y) .. " m" end
function M.lineto(x, y) path[#path + 1] = P(x, y) .. " l" end
function M.curveto(x1, y1, x2, y2, x3, y3) path[#path + 1] = P(x1, y1) .. " " .. P(x2, y2) .. " " .. P(x3, y3) .. " c" end
function M.close() path[#path + 1] = "h" end
function M.poly(pts, closed)
  path[#path + 1] = P(pts[1][1], pts[1][2]) .. " m"
  for i = 2, #pts do path[#path + 1] = P(pts[i][1], pts[i][2]) .. " l" end
  if closed then path[#path + 1] = "h" end
end
function M.smooth(pts, closed, tension)
  local n = #pts
  if n < 3 then return M.poly(pts, closed) end
  local k = (tension or 1) / 6
  local function at(i)
    if closed then return pts[(i - 1) % n + 1] end
    return pts[math.max(1, math.min(n, i))]
  end
  path[#path + 1] = P(pts[1][1], pts[1][2]) .. " m"
  local last = closed and n or n - 1
  for i = 1, last do
    local p0, p1, p2, p3 = at(i - 1), at(i), at(i + 1), at(i + 2)
    path[#path + 1] = P(p1[1] + (p2[1] - p0[1]) * k, p1[2] + (p2[2] - p0[2]) * k) .. " " ..
      P(p2[1] - (p3[1] - p1[1]) * k, p2[2] - (p3[2] - p1[2]) * k) .. " " .. P(p2[1], p2[2]) .. " c"
  end
  if closed then path[#path + 1] = "h" end
end
function M.circle(x, y, r)
  local k = 0.5523 * r
  path[#path + 1] = P(x + r, y) .. " m " .. P(x + r, y + k) .. " " .. P(x + k, y + r) .. " " .. P(x, y + r) .. " c " ..
    P(x - k, y + r) .. " " .. P(x - r, y + k) .. " " .. P(x - r, y) .. " c " ..
    P(x - r, y - k) .. " " .. P(x - k, y - r) .. " " .. P(x, y - r) .. " c " ..
    P(x + k, y - r) .. " " .. P(x + r, y - k) .. " " .. P(x + r, y) .. " c h"
end
local function take() local s = concat(path, " ") path = {} return s end

local function rgb(c, stroke) return fmt(stroke and "%.3f %.3f %.3f RG" or "%.3f %.3f %.3f rg", c[1], c[2], c[3]) end

-- paint the current path. opacity < 1 or mult=true wraps it in its own graphics state
function M.fill(c, op, mult)
  local g = gs(op or 1, mult)
  if g then put("q /" .. g .. " gs " .. rgb(c) .. " " .. take() .. " f Q")
  else put(rgb(c) .. " " .. take() .. " f") end
end
-- dash: a PDF dash array, e.g. "[2 2] 0"
function M.stroke(c, w, op, mult, dash)
  local g = gs(op or 1, mult)
  local s = rgb(c, true) .. fmt(" %.2f w ", w) .. (dash and dash .. " d " or "") .. take() .. " S"
  if g then put("q /" .. g .. " gs " .. s .. " Q") else put("q " .. s .. " Q") end
end
-- clip to the current path until the matching unclip()
function M.clip() put("q " .. take() .. " W n") end
function M.unclip() put("Q") end
function M.discard() path = {} end
-- paint the whole of the current clip (inside a clip(), cheaper than repeating the path)
function M.flood(c, x0, y0, x1, y1)
  M.poly({ { x0, y0 }, { x1, y0 }, { x1, y1 }, { x0, y1 } }, true)
  M.fill(c)
end

-- write all layers (in order) as one literal node at the current position
local function literal(parts)
  if #parts == 0 then return 0 end
  local s = "q 1 J 1 j\n" .. concat(parts, "\n") .. "\nQ"
  local n = node.new("whatsit", "pdf_literal")
  n.mode = 0
  n.data = s
  node.write(n)
  return #s
end
local function sorted_keys()
  local keys = {}
  for k in pairs(layers) do keys[#keys + 1] = k end
  table.sort(keys)
  return keys
end
function M.flush()
  local parts = {}
  for _, k in ipairs(sorted_keys()) do parts[#parts + 1] = concat(layers[k], "\n") end
  layers, tags = {}, {}
  return literal(parts)
end

-- hand over what was recorded instead of writing it: { keys, layers, tags }
function M.take_recording()
  local rec = { keys = sorted_keys(), layers = layers, tags = tags }
  layers, tags, recording, tag = {}, {}, false, nil
  return rec
end
-- write one frame of a recording: the untagged pieces and those keep(tag) accepts
function M.emit(rec, keep)
  local parts = {}
  for _, k in ipairs(rec.keys) do
    local L, T, out = rec.layers[k], rec.tags[k], {}
    for i = 1, #L do
      local t = T[i]
      if t == nil or keep(t) then out[#out + 1] = L[i] end
    end
    if #out > 0 then parts[#parts + 1] = concat(out, "\n") end
  end
  return literal(parts)
end

-- ---------------------------------------------------------------- geometry
-- polyline helpers: points are {x,y}; `spine` functions return x,y for v in [0,1]

-- outward normals and cumulative length of a polyline
local function normals(pts)
  local n, out = #pts, {}
  for i = 1, n do
    local a, b = pts[math.max(1, i - 1)], pts[math.min(n, i + 1)]
    local dx, dy = b[1] - a[1], b[2] - a[2]
    local L = sqrt(dx * dx + dy * dy)
    if L < 1e-9 then L = 1 end
    out[i] = { -dy / L, dx / L }
  end
  return out
end
M.normals = normals

function M.arclen(pts)
  local s, acc = { 0 }, 0
  for i = 2, #pts do acc = acc + sqrt((pts[i][1] - pts[i - 1][1]) ^ 2 + (pts[i][2] - pts[i - 1][2]) ^ 2) s[i] = acc end
  return s, acc
end

-- a ribbon along a centerline: width(u) is the full width at fraction u of the length.
-- Returns the closed outline (left side forward, right side back).
function M.ribbon(pts, width)
  local nrm = normals(pts)
  local s, L = M.arclen(pts)
  local left, right = {}, {}
  for i, p in ipairs(pts) do
    local w = width(L > 0 and s[i] / L or 0) / 2
    left[#left + 1] = { p[1] + nrm[i][1] * w, p[2] + nrm[i][2] * w }
    right[#right + 1] = { p[1] - nrm[i][1] * w, p[2] - nrm[i][2] * w }
  end
  local out = left
  for i = #right, 1, -1 do out[#out + 1] = right[i] end
  return out
end

-- a tapered stroke along one cubic Bézier, as a closed outline of two Béziers:
-- the control points are pushed out along the curve's normals by half the
-- width at their parameter (w0 at the start, w1 at the end). Five times
-- smaller than a sampled ribbon and indistinguishable for a gentle curve.
function M.taper(x0, y0, x1, y1, x2, y2, x3, y3, w0, w1)
  local function nrm(dx, dy) local L = sqrt(dx * dx + dy * dy) if L < 1e-9 then return 0, 0 end return -dy / L, dx / L end
  local n0x, n0y = nrm(x1 - x0, y1 - y0)
  local n1x, n1y = nrm(x2 - x0, y2 - y0)
  local n2x, n2y = nrm(x3 - x1, y3 - y1)
  local n3x, n3y = nrm(x3 - x2, y3 - y2)
  local h0, h1, h2, h3 = w0 / 2, (2 * w0 + w1) / 6, (w0 + 2 * w1) / 6, w1 / 2
  path[#path + 1] = P(x0 + n0x * h0, y0 + n0y * h0) .. " m " ..
    P(x1 + n1x * h1, y1 + n1y * h1) .. " " .. P(x2 + n2x * h2, y2 + n2y * h2) .. " " .. P(x3 + n3x * h3, y3 + n3y * h3) .. " c " ..
    P(x3 - n3x * h3, y3 - n3y * h3) .. " l " ..
    P(x2 - n2x * h2, y2 - n2y * h2) .. " " .. P(x1 - n1x * h1, y1 - n1y * h1) .. " " .. P(x0 - n0x * h0, y0 - n0y * h0) .. " c h"
end

-- Catmull-Rom samples through control points {{x,y},...}, `per` per segment
function M.catmull(pts, per)
  local out, n = {}, #pts
  for i = 1, n - 1 do
    local p0, p1, p2, p3 = pts[math.max(i - 1, 1)], pts[i], pts[i + 1], pts[math.min(i + 2, n)]
    for k = 0, per - 1 do
      local t = k / per local t2, t3 = t * t, t * t * t
      local function c(j) return 0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) end
      out[#out + 1] = { c(1), c(2) }
    end
  end
  out[#out + 1] = { pts[n][1], pts[n][2] }
  return out
end

-- sample a curve function f(v) -> x,y at n+1 points
function M.sample(f, n, v0, v1)
  v0, v1 = v0 or 0, v1 or 1
  local out = {}
  for i = 0, n do local x, y = f(v0 + (v1 - v0) * i / n) out[#out + 1] = { x, y } end
  return out
end

-- quadratic and cubic Bézier evaluators, returning functions of v
function M.bezier3(x0, y0, x1, y1, x2, y2, x3, y3)
  return function(v)
    local u = 1 - v
    local a, b, c, d = u * u * u, 3 * u * u * v, 3 * u * v * v, v * v * v
    return a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3
  end
end

-- a blade: closed outline around a spine with half-widths wl(v), wr(v) on each side
-- and an optional edge perturbation e(v, side) added along the normal.
-- Used for petals, leaves, sepals, buds.
function M.blade(spine, n, wl, wr, edge)
  local c = M.sample(spine, n)
  local nrm = normals(c)
  local left, right = {}, {}
  for i = 1, n + 1 do
    local v = (i - 1) / n
    local el, er = 0, 0
    if edge then el, er = edge(v, 1), edge(v, -1) end
    local a, b = wl(v) + el, wr(v) + er
    if a < 0 then a = 0 end
    if b < 0 then b = 0 end
    left[i] = { c[i][1] + nrm[i][1] * a, c[i][2] + nrm[i][2] * a }
    right[i] = { c[i][1] - nrm[i][1] * b, c[i][2] - nrm[i][2] * b }
  end
  local out = {}
  for i = 1, n + 1 do out[#out + 1] = left[i] end
  for i = n, 2, -1 do out[#out + 1] = right[i] end
  return out, c, nrm
end

-- an irregular blob: a circle of radius r whose radius wobbles by `rough`
function M.blob(rng, x, y, rx, ry, rough, n)
  n = n or 9
  local ph, ph2, rot = rng.range(0, 2 * pi), rng.range(0, 2 * pi), rng.range(0, 2 * pi)
  local out = {}
  for i = 0, n - 1 do
    local a = 2 * pi * i / n
    local k = 1 + rough * (0.6 * sin(2 * a + ph) + 0.4 * sin(3 * a + ph2)) + rough * 0.5 * rng.sym(1)
    local px, py = rx * k * cos(a), ry * k * sin(a)
    out[#out + 1] = { x + px * cos(rot) - py * sin(rot), y + px * sin(rot) + py * cos(rot) }
  end
  return out
end

M.CM = CM
return M
