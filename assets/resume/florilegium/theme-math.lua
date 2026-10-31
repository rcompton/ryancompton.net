-- theme-math.lua -- a theme for florilegium that is not a plant: mathematics
-- cascading down the margin and across the bottom of the page.
-- Copyright (c) 2026 Kevin Raymond. MIT License: see LICENSE or florilegium.sty.
--
-- Shapes, symbols and equations, overlapping a little so they blend:
--   - in the corner where the column meets the bottom, one large figure: an
--     Apollonian gasket, a deep Koch snowflake, Vogel's disc, a polyhedron;
--   - down the column, one or two families flowing toward that corner, growing as
--     they go (the Koch snowflake gaining a level, a polygon gaining sides, the
--     cube truncating into the octahedron), joined by small copper arrows;
--   - along the bottom and under the text on the last page, equations that hold
--     (e^{iπ} + 1 = 0, V - E + F = 2, ...), set by TeX;
--   - and everywhere else, largest hole first, the figures of figures.lua, letters,
--     numerals and symbols set by TeX at many sizes and a slight tilt, and dots.
-- Like the garden, it fills whatever space the page leaves: the column, the band
-- along the bottom, the space under the text. density sets how many things there
-- are; at 0.05 the corner figure and a few symbols.
-- Use: \usepackage[grown,theme=math]{florilegium}.

local ink = require("ink")
local figs = require("figures")
local FIG, FAM = figs.figures, figs.families
local M = {}

local sin, cos, sqrt, pi, abs, floor, max, min = math.sin, math.cos, math.sqrt, math.pi, math.abs, math.floor, math.max, math.min
local tone = ink.tone
local rad = pi / 180

-- ---------------------------------------------------------------- what is set in TeX
local GLYPHS = {
  "\\mathrm{A}", "\\mathrm{M}", "\\mathrm{Q}", "\\mathrm{B}", "\\mathrm{D}", "\\mathcal{F}", "\\mathcal{L}", "\\mathcal{R}",
  "x", "y", "n", "k", "e", "i", "z",
  "0", "1", "2", "3", "4", "5", "7", "8", "9",
  "+", "=", "-", "\\times", "\\pm", "(", ")", "[", "]", "!", "\\approx", "\\in", "\\le",
  "\\pi", "\\varphi", "\\lambda", "\\theta", "\\Omega", "\\Delta", "\\Sigma", "\\partial", "\\nabla", "\\infty", "\\aleph",
  "\\displaystyle\\int", "\\displaystyle\\sum", "\\displaystyle\\prod", "\\displaystyle\\oint", "\\sqrt{\\;}",
}
local EQUATIONS = {
  "e^{i\\pi}+1=0", "a^2+b^2=c^2", "\\varphi^2=\\varphi+1", "V-E+F=2", "i^2=-1",
  "\\sum_{n\\ge1}\\frac{1}{n^2}=\\frac{\\pi^2}{6}", "\\int_{-\\infty}^{\\infty}e^{-x^2}dx=\\sqrt{\\pi}",
  "F_{n+1}=F_n+F_{n-1}", "\\cos^2\\theta+\\sin^2\\theta=1", "x=\\frac{-b\\pm\\sqrt{b^2-4ac}}{2a}",
  "e^x=\\sum_{n\\ge0}\\frac{x^n}{n!}", "e=\\sum_{n\\ge0}\\frac{1}{n!}", "\\frac{d}{dx}e^x=e^x",
  "1+2+\\cdots+n=\\frac{n(n+1)}{2}", "\\zeta(s)=\\prod_p\\frac{1}{1-p^{-s}}", "z\\mapsto z^2+c",
  "\\lim_{n\\to\\infty}\\bigl(1+\\frac1n\\bigr)^n=e", "\\pi\\approx\\frac{355}{113}", "\\dim=\\log_3 4",
  "r=\\cos k\\theta", "\\oint_C f\\,dz=0", "2^{\\aleph_0}>\\aleph_0", "n\\sin\\frac{\\pi}{n}\\to\\pi",
}
-- the width of TeX at 10 pt, in cm, roughly: the characters that show
local function width(t)
  t = t:gsub("\\[a-zA-Z]+", "x"):gsub("[{}$^_\\]", "")
  return #t * 0.2
end

-- ---------------------------------------------------------------- the page
-- Called by grow.page with the page (g) and grow.lua. Returns { captions = ... }
-- (and { rec, total } in the animation), the TeX in layout cm for florilegium.lua.
function M.page(g, grow)
  local rng = ink.rng(g.seed * 7919 + 41)
  local layout = rng.fork()
  ink.set_transform(ink.page_transform(g.mirror and g.pw))
  local D = g.density or 1
  local anim = g.anim
  if anim then ink.record(true) end
  local _, col, foot, spill = grow.regions(g, layout)
  -- the band along the bottom runs further than the garden's footer
  foot = { foot[1], foot[2], g.textleft + (g.textright - g.textleft) * 0.72, foot[4] }
  local regions = { col, foot, spill }
  local fld = grow.field(regions)
  local gx, gy, free, disc, free_at = fld.x, fld.y, fld.free, fld.disc, fld.free_at
  disc(g.colright - 0.5, g.headrule + 0.1, 0.7, 1)        -- the header's fleuron
  local fwd = g.mirror and -1 or 1                         -- the reading direction, in layout x
  local captions, events = {}, {}
  local counts = {}
  for _, n in ipairs(figs.figure_order) do counts[n] = 0 end

  local BLOOM = { 0.3, 0.55, 0.75, 0.9 }
  local function event()
    local e = { t0 = 0.3 + 0.12 * #events, dur = 0.35 }
    events[#events + 1] = e
    return e
  end
  local function place(e, x, y, fn)
    ink.layer(5)
    if anim then
      local r0, l0 = rng.save(), layout.save()
      for k = 1, #BLOOM do
        ink.tag({ e, (k - 1) / #BLOOM, k / #BLOOM })
        ink.push() ink.translate(x, y) ink.scale(BLOOM[k]) fn() ink.pop()
        rng.load(r0) layout.load(l0)
      end
      ink.tag({ e, 1 })
    end
    ink.push() ink.translate(x, y) fn() ink.pop()
    if anim then ink.tag({ e, 0 }) end
  end
  local function figure(name, x, y, R, accent)
    local f = FIG[name]
    local p = f.pick(layout)
    place(event(), x, y, function()
      if accent then ink.in_accent(function() f.draw(rng.fork(), R, p) end) else f.draw(rng.fork(), R, p) end
    end)
    counts[name] = (counts[name] or 0) + 1
  end
  -- a symbol in TeX, about 2r tall, a little tilted, in one of the ink's tones or copper
  local COLORS = { 0.06, 0.1, 0.22, 0.35, 0.5 }
  local function glyph(x, y, r)
    local t = GLYPHS[layout.int(1, #GLYPHS)]
    local c = layout.chance(0.15) and ink.accent(0) or tone(COLORS[layout.int(1, #COLORS)])
    local big = t:find("displaystyle") and 2.2 or 1                -- the big operators stand taller
    captions[#captions + 1] = { x = x, y = y, text = "$" .. t .. "$", anchor = "center", scale = r / (0.14 * big),
      rotate = layout.sym(18), color = c, opacity = 0.92, event = event() }
  end
  local function dot(x, y, r)
    local ring, copper = layout.chance(0.4), layout.chance(0.3)
    local t = layout.range(0.3, 0.8)
    place(event(), x, y, function()
      local c = copper and ink.accent(0) or tone(t)
      ink.circle(0, 0, r)
      if ring then ink.stroke(c, 0.5) else ink.fill(c, 0.85, true) end
    end)
  end
  local function inside(r, x, y) return x > r[1] and x < r[3] and y > r[2] and y < r[4] end

  -- 1. the corner figure, where the column meets the bottom
  local cw = col[3] - col[1]
  do
    local R = min(2.1, cw * 0.36) * (0.7 + 0.3 * D)
    local x, y = col[1] + R + 0.15, col[2] + R + 0.1
    local name = ({ "gasket", "koch", "vogel", "polyhedron", "chords" })[layout.int(1, 5)]
    if free_at(x, y) >= R * 0.9 then
      if name == "koch" then
        local p = { layout.range(0, 120), 4 }
        place(event(), x, y, function() FIG.koch.draw(rng.fork(), R, p) end)
      else figure(name, x, y, R) end
      disc(x, y, R, 0.95)
    end
  end

  -- marks: a small copper figure beside each heading; \florilegiumbloom[name] a figure
  for _, mk in ipairs(g.marks or {}) do
    local heading = mk.kind == "heading"
    local R = heading and (mk.arg == 1 and 0.42 or 0.32) or 0.6
    local x, y = g.colright - R - 0.25, mk.y + 0.12
    if free_at(x, y) >= R + 0.05 then
      figure(heading and "hypotrochoid" or (FIG[mk.arg] and mk.arg or "maurer"), x, y, R, heading)
      disc(x, y, R + 0.1, 1)
    end
  end

  -- 2. families flowing down the column toward the corner, each figure larger
  -- than the one before, joined by small copper arrows
  local nfam = D >= 0.5 and 2 or D >= 0.15 and 1 or 0
  for f = 1, nfam do
    local name = figs.family_order[layout.int(1, #figs.family_order)]
    local fam = FAM[name]
    local k = min(#fam.values, layout.int(3, 5))
    local first = layout.int(1, #fam.values - k + 1)
    local p = fam.pick(layout)
    local R0, grow_by = layout.range(0.25, 0.38), layout.range(1.15, 1.3)
    local sway, ph = layout.range(0.2, 0.6), layout.range(0, 2 * pi)
    local top = col[4] - 0.4 - (f - 1) * (col[4] - col[2]) * layout.range(0.3, 0.45)
    local x0 = col[1] + cw * layout.range(0.3, 0.7)
    -- the highest start in this stretch where the whole run fits
    local best
    for y0 = top, col[2] + 4, -0.2 do
      local pts, y, R, ok = {}, y0, R0, true
      for i = 1, k do
        local x = x0 + sway * sin(ph + 1.3 * i)
        if free_at(x, y) < R + 0.12 then ok = false break end
        pts[i] = { x, y, R }
        y = y - R - 0.45 - R * grow_by
        R = R * grow_by
      end
      if ok then best = pts break end
    end
    if best then
      local bow = layout.sym(0.08)
      for i, c in ipairs(best) do
        local v = fam.values[first + i - 1]
        local e = event()
        place(e, c[1], c[2], function() fam.draw(rng.fork(), c[3], v, p) end)
        if i > 1 then
          local a = best[i - 1]
          local dx, dy = c[1] - a[1], c[2] - a[2]
          local L = sqrt(dx * dx + dy * dy)
          dx, dy = dx / L, dy / L
          local x0a, y0a, x1, y1 = a[1] + dx * (a[3] + 0.08), a[2] + dy * (a[3] + 0.08), c[1] - dx * (c[3] + 0.08), c[2] - dy * (c[3] + 0.08)
          local mx, my = (x0a + x1) / 2 - dy * bow, (y0a + y1) / 2 + dx * bow
          ink.layer(4)
          if anim then ink.tag({ e, 0 }) end
          ink.moveto(x0a, y0a) ink.curveto(mx, my, mx, my, x1, y1) ink.stroke(ink.accent(0), 0.3, 0.9)
          local tx, ty = x1 - mx, y1 - my
          local tl = sqrt(tx * tx + ty * ty)
          tx, ty = tx / tl, ty / tl
          ink.poly({ { x1, y1 }, { x1 - tx * 0.09 - ty * 0.035, y1 - ty * 0.09 + tx * 0.035 }, { x1 - tx * 0.09 + ty * 0.035, y1 - ty * 0.09 - tx * 0.035 } }, true)
          ink.fill(ink.accent(0))
          if anim then ink.tag(nil) end
        end
        disc(c[1], c[2], c[3] + 0.08, 1)
      end
    end
  end

  -- 3. equations along the bottom and in the space under the text, in reading order
  local used = {}
  local function equation(maxw, scale)
    for _ = 1, 8 do
      local i = layout.int(1, #EQUATIONS)
      if not used[i] and width(EQUATIONS[i]) * scale <= maxw then used[i] = true return EQUATIONS[i] end
    end
  end
  local function line(region, y, scale, x_from)
    -- equations one after another along y, as far as they fit, smaller as they go
    local x = x_from
    local stop = fwd > 0 and region[3] - 0.2 or region[1] + 0.2
    local h = 0.42 * scale
    while (stop - x) * fwd > 1.0 do
      local t = equation((stop - x) * fwd, scale)
      if not t then break end
      local w = width(t) * scale
      local x1 = x + fwd * w
      local ok = true
      for u = 0, 1.001, 0.25 do
        if free_at(x + fwd * w * u, y) < h * 0.4 then ok = false break end
      end
      if ok then
        captions[#captions + 1] = { x = x, y = y, text = "$" .. t .. "$", anchor = fwd > 0 and "west" or "east", scale = scale,
          color = tone(layout.range(0.06, 0.25)), event = event() }
        for u = 0, 1.001, 0.1 do disc(x + fwd * w * u, y, h * 0.7, 1) end
        x = x1 + fwd * layout.range(0.5, 1.0)
      else
        x = x + fwd * 0.6
      end
      scale = scale * 0.92
    end
  end
  if D >= 0.1 then
    local fy = (foot[2] + foot[4]) / 2
    local start = fwd > 0 and foot[1] + 0.4 or foot[3] - 0.4
    line(foot, fy, 1.15, start)
  end
  if spill then
    local rows = max(1, floor((spill[4] - spill[2]) / 4.5 * D + 0.5))
    for r = 1, rows do
      local y = spill[4] - 0.5 - (spill[4] - spill[2] - 0.8) * (r - 0.5) / rows + layout.sym(0.3)
      local start = fwd > 0 and spill[1] + layout.range(0.3, 2.5) or spill[3] - layout.range(0.3, 2.5)
      line(spill, y, layout.range(1.0, 1.35), start)
    end
  end

  -- 4. the rest, largest hole first: a figure, a symbol or a dot, overlapping a
  -- little so that they blend
  local area = 0
  for _, r in ipairs(regions) do area = area + (r[3] - r[1]) * (r[4] - r[2]) end
  local NMAX = floor(D * area / 2.8 + 0.5)
  local MINF = 0.16 / sqrt(D)
  local n = 0
  while n < NMAX do
    local best, bi = -1, nil
    for i = 1, #gx do
      local v = free[i] * layout.range(0.85, 1.15)
      if v > best then best, bi = v, i end
    end
    if not bi or free[bi] < MINF then break end
    local f, x, y = free[bi], gx[bi], gy[bi]
    -- larger toward the corner, smaller up the column and out along the bottom
    local reach = (y - col[2]) / (col[4] - col[2]) + max(0, (x - col[3]) * fwd) / max(1, foot[3] - foot[1])
    f = f * (1.1 - 0.5 * min(1, reach))
    local u = layout.u()
    if f > 0.55 and u < 0.45 then
      -- a figure, not one there are already two of
      local name
      for _ = 1, 6 do
        local c = figs.figure_order[layout.int(1, #figs.figure_order)]
        if counts[c] < 2 then name = c break end
      end
      local R = min(f * 0.95, 1.25)
      if name and R >= FIG[name].r[1] * 0.6 then figure(name, x, y, R) disc(x, y, R, 0.62)
      else glyph(x, y, min(f, 0.6)) disc(x, y, min(f, 0.6), 0.5) end
    elseif f > 0.22 and u < 0.88 then
      local r = min(f, 0.6) * layout.range(0.6, 1.0)
      glyph(x, y, r)
      disc(x, y, r, 0.5)
    else
      local r = min(f, 0.25) * layout.range(0.3, 0.6)
      dot(x, y, r)
      disc(x, y, max(r, 0.15), 0.8)
    end
    n = n + 1
  end

  if texio then texio.write_nl(string.format("florilegium: %d marks of mathematics", #events)) end
  if anim then
    local total = 0
    for _, e in ipairs(events) do total = max(total, e.t0 + e.dur) end
    return { rec = ink.take_recording(), total = max(total, 0.5), captions = captions }
  end
  ink.flush()
  return { captions = captions }
end

-- every figure and family member on its own too: \florilegiumdraw{knot}{1.2}
M.flora = { hedera = figs.compass }
for _, name in ipairs(figs.figure_order) do
  local f = FIG[name]
  M.flora[name] = function(rng, R, o) f.draw(rng, R, (o and o.p) or f.pick(rng)) end
end
for _, name in ipairs(figs.family_order) do
  local f = FAM[name]
  if not M.flora[name] then
    M.flora[name] = function(rng, R, o) o = o or {} f.draw(rng, R, o.v or f.values[1], o.p or f.pick(rng)) end
  end
end

return M
