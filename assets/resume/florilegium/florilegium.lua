-- florilegium.lua -- the TeX-facing side of florilegium.sty: page geometry,
-- colors, seeds, the TikZ transform, and the dispatch of primitives.
-- Copyright (c) 2026 Kevin Raymond. MIT License: see LICENSE or florilegium.sty.

local ink = require("ink")
local flora = require("flora")
local M = { ink = ink, flora = flora }

local SP_CM = 2.54 / (72.27 * 65536)          -- cm per scaled point
local function cm(name) return tex.dimen[name] * SP_CM end

-- the page layout, in cm from the lower-left corner of the paper. The garden
-- grows in the wider side margin: when that is the right one (the outer margin
-- of a right-hand page in a two-sided document), the layout is made for the
-- mirrored page and drawn reflected (g.mirror; ink.page_transform).
M.twoside = false                             -- \if@twoside, set at each shipout
function M.geometry()
  local inch = 2.54
  local even = M.twoside and tex.count[0] % 2 == 0
  local g = {
    pw = cm("paperwidth"), ph = cm("paperheight"),
    textleft = inch + tex.hoffset * SP_CM + cm(even and "evensidemargin" or "oddsidemargin"),
  }
  g.textright = g.textleft + cm("textwidth")
  if g.pw - g.textright > g.textleft + 0.05 then
    g.mirror = true
    g.textleft, g.textright = g.pw - g.textright, g.pw - g.textleft
  end
  g.ytop = g.ph - inch - cm("topmargin") - cm("headheight") - cm("headsep")
  g.ybot = g.ytop - cm("textheight")
  g.colright = g.textleft - 0.4
  g.headrule = g.ytop + cm("headsep") - 0.1
  g.footy = g.ybot - cm("footskip")
  return g
end

-- colors: `ink` sets the hue of the whole ramp, `accent` the copper
local current = { 0x24 / 255, 0x56 / 255, 0xC4 / 255, 0.71, 0.40, 0.18 }
function M.colors(ir, ig, ib, ar, ag, ab)
  current = { ir, ig, ib, ar, ag, ab }
  ink.set_ink(ir, ig, ib)
  ink.set_accent(ar, ag, ab)
end

-- one rng per page; primitives drawn from TeX fork it in call order
local page_rng = ink.rng(1)
function M.seed(page, fixed)
  local s = fixed and (fixed * 7919 + page * 131) or (page * 97 + 1030)
  page_rng = ink.rng(s)
  return s
end

-- the current pgf transformation (TikZ scopes) as an ink transform: local cm -> page bp
local function sync_transform()
  local C = ink.CM
  local bp = 72 / 72.27 / 65536
  ink.set_transform({
    tonumber(token.get_macro("pgf@pt@aa")) * C, tonumber(token.get_macro("pgf@pt@ab")) * C,
    tonumber(token.get_macro("pgf@pt@ba")) * C, tonumber(token.get_macro("pgf@pt@bb")) * C,
    tex.dimen["pgf@pt@x"] * bp, tex.dimen["pgf@pt@y"] * bp })
end

-- \florilegiumdraw{name}{s, opts}: one primitive at the origin of the current TikZ
-- scope; the names of the current theme's primitives work too
local scaled = { leaf = true, leaflet = true, petal = true }
local function primitives() return require("grow").theme(M.theme) end
function M.draw(name, s, o)
  local flora = primitives()
  local fn = flora[name]
  if not fn then tex.error("florilegium: unknown primitive '" .. tostring(name) .. "'") return end
  sync_transform()
  local rng = page_rng.fork()
  if name == "ghost" then
    flora.ghost(o and o.lift, function() M.draw_inner(s, o, rng) end)
  elseif scaled[name] then
    ink.scale(s or 1) fn(rng, o)
  else
    fn(rng, s, o)
  end
  ink.flush()
end
-- \florilegiumdraw{ghost}{"flower", {s=1.4}} draws any primitive pale
function M.draw_inner(name, o, rng)
  o = o or {}
  local flora = primitives()
  local fn = flora[name]
  if scaled[name] then ink.scale(o.s or 1) fn(rng, o) else fn(rng, o.s or 1, o) end
end

-- ---------------------------------------------------------------- ornaments in the text
-- \florilegiumornament[size, ink, accent, angle, seed]{name}: one primitive in a box
-- of side `size` (sp) on the baseline, like a letter (its depth 0.15 of the size).
-- Where each primitive sits in that box: its origin (x, y as fractions of the
-- side), its scale, its angle, and options for it.
local ORNAMENT = {
  leaf = { 0.2, 0.1, 1.02, -40 }, leaflet = { 0.2, 0.1, 1.0, -40 }, petal = { 0.3, 0.02, 1.0, -30 },
  bud = { 0.35, 0.0, 0.95, -20 }, bell = { 0.5, 0.97, 0.95, 0 }, sprig = { 0.4, 0.0, 1.0, -10 },
  cyme = { 0.35, 0.0, 0.95, -10, { side = -1 } }, umbel = { 0.5, 0.05, 0.8, 0 }, tendril = { 0.95, 0.5, 0.45, 0 },
  flower = { 0.5, 0.5, 0.47, 0 }, blossom = { 0.5, 0.5, 0.48, 0 }, floret = { 0.5, 0.5, 0.46, 0 },
  lily = { 0.5, 0.45, 0.6, 0 }, seedhead = { 0.5, 0.42, 0.42, 0, { drift = 0 } },
  butterfly = { 0.5, 0.5, 0.98, 0 }, bee = { 0.5, 0.5, 0.8, -30, { trail = false } },
  snail = { 0.5, 0.35, 0.55, -90 }, bird = { 0.5, 0.02, 0.95, 0 },
  sparkle = { 0.5, 0.5, 0.3, 0 }, rosette = { 0.5, 0.5, 0.38, 0 }, hedera = { 0.45, 0.62, 0.36, 0 },
}
local function hex(h) return tonumber(h:sub(1, 2), 16) / 255, tonumber(h:sub(3, 4), 16) / 255, tonumber(h:sub(5, 6), 16) / 255 end
local nornament = 0
function M.ornament(name, size, inkhex, acchex, angle, seed)
  local flora = primitives()
  local fn = flora[name]
  if not fn then tex.error("florilegium: unknown primitive '" .. tostring(name) .. "'") return end
  nornament = nornament + 1
  -- the k-th ornament of the document always gets the same shape, unless a seed
  -- is given; seed=random gives a new one every time the document is built
  local s
  if seed == "random" then s = (os.time() % 999983) * 7919 + math.floor(os.clock() * 1e6) + nornament * 131
  elseif tonumber(seed) then s = tonumber(seed) * 7919 + 17
  else s = nornament * 7919 + 4243 end
  if inkhex ~= "" or acchex ~= "" then
    local c = current
    M.colors(inkhex ~= "" and hex(inkhex) or c[1], inkhex ~= "" and select(2, hex(inkhex)) or c[2], inkhex ~= "" and select(3, hex(inkhex)) or c[3],
      acchex ~= "" and hex(acchex) or c[4], acchex ~= "" and select(2, hex(acchex)) or c[5], acchex ~= "" and select(3, hex(acchex)) or c[6])
    current = c
  end
  local S = size * SP_CM
  local p = ORNAMENT[name] or { 0.5, 0.5, 0.46, 0 }
  ink.set_transform({ ink.CM, 0, 0, ink.CM, 0, 0 })
  ink.translate(S * p[1], S * (p[2] - 0.15))
  ink.rotate(p[4] + (angle or 0))
  if scaled[name] then ink.scale(S * p[3]) fn(ink.rng(s), p[5] or {})
  else fn(ink.rng(s), S * p[3], p[5] or {}) end
  ink.flush()
  if inkhex ~= "" or acchex ~= "" then M.colors(table.unpack(current)) end
end

-- the header: a copper ivy leaf (or the theme's fleuron) whose stem becomes the head rule
function M.head(g)
  ink.set_transform(ink.page_transform(g.mirror and g.pw))
  ink.push()
  ink.translate(g.colright - 0.55, g.headrule + 0.02)
  local x, y = primitives().hedera(page_rng.fork(), 0.36)
  if g.mirror then x = g.pw - x end           -- hedera answers on the page, not in the mirrored layout
  ink.pop()
  local e = g.textright
  ink.moveto(x, y) ink.curveto(x + 1.0, y, x + 1.5, g.headrule, x + 2.5, g.headrule) ink.lineto(e, g.headrule)
  ink.stroke(ink.accent(0), 0.4)
  ink.circle(e, g.headrule, 0.03) ink.fill(ink.accent(0))
  ink.flush()
end

-- ---------------------------------------------------------------- marks in the text
-- \florilegiumbloom[motif] and (option sections) the section headings leave a
-- whatsit in the text. The page box is searched for them at shipout, when the
-- garden is drawn, so the garden knows the height of those lines on the same
-- page in the same run.
local MARK = 0x464C4F                         -- "FLO"
local marks = {}
function M.mark(kind, arg)
  marks[#marks + 1] = { kind = kind, arg = arg }
  local n = node.new("whatsit", "user_defined")
  n.user_id, n.type, n.value = MARK, 100, #marks
  node.write(n)
end

local HLIST, VLIST, GLUE, KERN, RULE, WHATSIT = node.id("hlist"), node.id("vlist"), node.id("glue"), node.id("kern"), node.id("rule"), node.id("whatsit")
local USER = node.subtype("user_defined")
-- walk a box list; y grows downward from the top of the outer box, x rightward
local function walk(head, parent, x, y, vertical, out)
  for n in node.traverse(head) do
    local id = n.id
    if id == HLIST or id == VLIST then
      if vertical then
        local base = y + n.height
        if n.list then walk(n.list, n, x + n.shift, id == VLIST and y or base, id == VLIST, out) end
        y = base + n.depth
      else
        local base = y + n.shift
        if n.list then walk(n.list, n, x, id == VLIST and base - n.height or base, id == VLIST, out) end
        x = x + n.width
      end
    elseif id == GLUE then
      local w = node.effective_glue(n, parent)
      if vertical then y = y + w else x = x + w end
    elseif id == KERN then
      if vertical then y = y + n.kern else x = x + n.kern end
    elseif id == RULE then
      if vertical then y = y + n.height + n.depth else x = x + n.width end
    elseif id == WHATSIT and n.subtype == USER and n.user_id == MARK then
      local m = marks[n.value]
      if m then out[#out + 1] = { kind = m.kind, arg = m.arg, x = x, y = y } end
    elseif not vertical then
      x = x + node.dimensions(n, n.next)
    end
  end
end
-- the marks on the page being shipped out, in page cm from the lower-left corner
local function page_marks(box)
  local b = box and tex.box[box]
  if not b then return {} end
  local out = {}
  walk(b.list, b, 0, 0, b.id == VLIST, out)
  local ph, inch = tex.dimen.paperheight * SP_CM, 2.54
  for _, m in ipairs(out) do
    m.x = inch + tex.hoffset * SP_CM + m.x * SP_CM
    m.y = ph - inch - tex.voffset * SP_CM - m.y * SP_CM
  end
  return out
end

-- ---------------------------------------------------------------- initials
-- \florilegiuminitial: a tile of side `side` (sp) whose top is the cap height
-- above the current baseline and whose left edge is `hang` (sp) to the left of
-- the current point, the start of the paragraph's first, indented line.
M.initial_font = "lmroman10-bold.otf"
function M.initial(letter, side, hang, cap)
  local bp = 72 / 72.27 / 65536
  ink.set_transform({ ink.CM, 0, 0, ink.CM, -hang * bp, (cap - side) * bp })
  local ok, err = require("initial").draw(page_rng.fork(), side * SP_CM, letter, { font = M.initial_font })
  if not ok then tex.error("florilegium: " .. tostring(err)) end
  ink.flush()
end
-- the letter is also typeset in the text, in PDF's invisible text rendering
-- mode, so that the paragraph still copies and searches as "This", not "his"
function M.hidden(on)
  local n = node.new("whatsit", "pdf_literal")
  n.mode = 1                                  -- page level, outside the text object
  n.data = on and "3 Tr" or "0 Tr"
  node.write(n)
end

-- ---------------------------------------------------------------- aging
-- a garden's age: 0 spring (buds), 0.5 summer, 1 autumn (seed heads, falling
-- petals); nil leaves it as it always was. \florilegiumage sets it; the option
-- aging spreads it over the document, from the page count of the last run.
M.age = nil
function M.auto_age(page, last) M.age = last > 1 and math.min(1, (page - 1) / (last - 1)) or 0.5 end

-- the growth animation: after \florilegiumframe[explain]{k}{n}, a grown page
-- shows frame k of n of its garden's growth (animation.tex, tools/animate.py).
-- The garden is recorded once and each frame writes the part grown so far.
local frame, recorded = nil, {}
function M.frame(k, n, explain) frame = { k = k, n = n, explain = explain == "explain" } end

-- text a theme sets in the margin (captions, glyphs, equations): TeX nodes in the
-- margin picture at {x, y} in layout cm, by their anchor (default north: the top
-- of the text centered there). Small ones in 5.5 pt, others in 6.5 pt or, with
-- `scale`, 10 pt scaled; `rotate` (degrees), `color` ({r, g, b}), `opacity`. On a
-- mirrored page east and west trade places and rotations turn the other way.
local function captions(g, list, shown)
  if not list or #list == 0 then return end
  local c = ink.tone(0.12)
  local out = { string.format("\\definecolor{flocaption}{rgb}{%.3f,%.3f,%.3f}", c[1], c[2], c[3]) }
  for _, cap in ipairs(list) do
    if not shown or shown(cap) then
      local x = g.mirror and g.pw - cap.x or cap.x
      local anchor = cap.anchor or "north"
      if g.mirror then anchor = anchor:gsub("east", "\0"):gsub("west", "east"):gsub("\0", "west") end
      local opts = { "anchor=" .. anchor, "inner sep=0pt", "align=center" }
      if cap.color then
        opts[#opts + 1] = string.format("text={rgb,255:red,%d;green,%d;blue,%d}", math.floor(cap.color[1] * 255 + 0.5),
          math.floor(cap.color[2] * 255 + 0.5), math.floor(cap.color[3] * 255 + 0.5))
      else opts[#opts + 1] = "text=flocaption" end
      if cap.scale then
        opts[#opts + 1] = string.format("font=\\fontsize{10}{12}\\selectfont,scale=%.3f,transform shape", cap.scale)
      else
        opts[#opts + 1] = "font=\\fontsize{" .. (cap.small and "5.5}{6.5" or "6.5}{7.5") .. "}\\selectfont"
      end
      if cap.rotate and cap.rotate ~= 0 then opts[#opts + 1] = string.format("rotate=%.1f", g.mirror and -cap.rotate or cap.rotate) end
      if cap.opacity then opts[#opts + 1] = string.format("text opacity=%.2f", cap.opacity) end
      out[#out + 1] = string.format("\\node[%s] at (%.2f,%.2f) {%s};", table.concat(opts, ","), x, cap.y, cap.text)
    end
  end
  tex.sprint(table.concat(out))
end

local function grown_frame(g)
  local key = string.format("%d %d %.3f %s %d %s %s %s", g.seed, g.spill, g.spilly, tostring(g.age), #g.marks, tostring(g.theme), tostring(g.mirror), tostring(g.density))
  if not recorded[key] then
    g.anim = true
    recorded = { [key] = require("grow").page(g) }      -- keep only the latest garden
  end
  local r = recorded[key]
  -- the last frame is the page: every event finished (r.total itself may round below)
  local t = frame.k >= frame.n and math.huge or r.total * (frame.k - 1) / math.max(1, frame.n - 1)
  ink.emit(r.rec, function(tag)
    if tag.overlay and not frame.explain then return false end
    local e = tag[1]
    local p = (t - e.t0) / e.dur
    return p >= tag[2] and (tag[3] == nil or p < tag[3])
  end)
  captions(g, r.captions, function(cap) return t >= cap.event.t0 + cap.event.dur end)
end

-- the theme (option theme=...): nil is flora; otherwise theme-<name>.lua replaces
-- some of the primitives (grow.lua). In the document, \florilegiumtheme leaves a
-- mark, so the theme changes from the page that the mark is on.
M.theme = nil
local function themes(marks)
  local rest = {}
  for _, m in ipairs(marks) do
    if m.kind == "theme" then M.theme = m.arg ~= "" and m.arg or nil else rest[#rest + 1] = m end
  end
  return rest
end

-- how much is in the margin (options density and intensity, 0..1): density thins
-- the grown garden out, intensity < 1 paints the whole margin paler, as the
-- ghost layer is painted (1 - intensity of the way to the paper, at most 85%)
M.density, M.intensity = 1, 1
local function pale() return 0.85 * (1 - math.max(0, math.min(1, M.intensity))) end

-- the grown composition for this page; M.visitors = false (option novisitors)
-- leaves out the butterflies, bees, snails and birds
M.visitors = true
function M.grown(seed, spill, spilly, box)
  local g = M.geometry()
  g.marks = themes(page_marks(box))
  g.seed, g.spill, g.spilly, g.visitors, g.age, g.theme = seed, spill, spilly, M.visitors, M.age, M.theme
  if M.density < 1 then g.density = math.max(0.03, M.density) end
  local old = ink.set_pale(pale())
  if frame then grown_frame(g)
  else
    local r = require("grow").page(g)
    captions(g, r and r.captions)
  end
  M.head(g)
  ink.set_pale(old)
end

-- the authored composition for this page (intensity applies; density does not,
-- everything here is placed by hand)
function M.authored(seed, box)
  themes(page_marks(box))
  local g = M.geometry()
  g.seed, g.visitors, g.theme = seed, M.visitors, M.theme
  local old = ink.set_pale(pale())
  local r = require("authored").page(g)
  captions(g, r and r.captions)
  M.head(g)
  ink.set_pale(old)
end

return M
