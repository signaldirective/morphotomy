-- MORPHOTOMY · graft line, suture timing
-- The active border is the incision: arterial red pulled tight into dried blood.

local active_border = { colors = { "rgba(ff2e3df0)", "rgba(7d0a10e0)" }, angle = 45 }
local inactive_border = "rgba(4a1c22aa)"
local graft_shadow = "rgba(ff2e3d26)"
local dead_shadow = "rgba(00000060)"

hl.config({
  general = {
    gaps_in = 4,
    gaps_out = 8,
    border_size = 2,
    resize_on_border = true,
    col = {
      active_border = active_border,
      inactive_border = inactive_border,
    },
  },

  group = {
    col = {
      border_active = active_border,
      border_inactive = inactive_border,
    },
  },

  decoration = {
    rounding = 2,
    shadow = {
      enabled = true,
      range = 10,
      render_power = 3,
      color = graft_shadow,
      color_inactive = dead_shadow,
    },
    blur = {
      enabled = false,
    },
  },

  animations = {
    enabled = true,
  },
})

-- Two curves: the pull of a suture, and the cut of an incision.
hl.curve("suture", { type = "bezier", points = { { 0.14, 0.96 }, { 0.07, 1.0 } } })
hl.curve("incision", { type = "bezier", points = { { 0.55, 0.0 }, { 0.95, 0.35 } } })

hl.animation({ leaf = "windows", enabled = true, speed = 4.2, bezier = "suture" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4.4, bezier = "suture", style = "popin 88%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 3.6, bezier = "incision", style = "popin 94%" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 4.4, bezier = "suture" })
hl.animation({ leaf = "border", enabled = true, speed = 6.5, bezier = "suture" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 5.2, bezier = "incision" })
hl.animation({ leaf = "fade", enabled = true, speed = 5.0, bezier = "incision" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 4.5, bezier = "suture", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 3.2, bezier = "incision", style = "fade" })
