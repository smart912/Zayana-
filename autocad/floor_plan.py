"""Hand-drawn FLOOR PLAN (scale 1:100) traced into an AutoCAD DXF.

Every wall, door, window and piece of furniture was measured on the original
sketch (pixel coordinates of the photo, read at 4-6x zoom) and is placed exactly
there.  One uniform scale converts the sketch so the plot is 26.00 m x 22.00 m.
Nothing is moved, added or re-arranged.

Units: metres (1 drawing unit = 1 m).  Origin = bottom-left corner of the plot.
Run:  python3 floor_plan.py   ->  floor_plan.dxf  (+ floor_plan_preview.png)
"""
import math
import random
from pathlib import Path

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from shapely import affinity
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union

OUT = Path(__file__).with_name("floor_plan.dxf")

# ------------------------------------------------------------------ sketch pixels -> metres
# plot wall centre-lines on the photo: x 185..1203 px, y 240..1103 px  ->  26 m x 22 m
PX0, PX1, PY0, PY1 = 185, 1203, 240, 1103
PLOT_W, PLOT_H = 26.0, 22.0
SX, SY = PLOT_W / (PX1 - PX0), PLOT_H / (PY1 - PY0)   # 0.0255 m per pixel both ways


def P(px, py):
    """photo pixel -> drawing metres (y flipped)."""
    return ((px - PX0) * SX, (PY1 - py) * SY)


def L(n_px):
    return n_px * (SX + SY) / 2


# ------------------------------------------------------------------ document
doc = ezdxf.new("R2010", setup=True)
doc.units = units.M
doc.header["$INSUNITS"] = 6
doc.header["$MEASUREMENT"] = 1
msp = doc.modelspace()
LAYERS = {
    "A-WALL": (7, 50), "A-WALL-HATCH": (8, 0), "A-SITE-WALL": (7, 35), "A-DOOR": (30, 18),
    "A-WINDOW": (4, 18), "A-STAIR": (2, 18), "A-FURN": (9, 13), "A-FURN-HATCH": (8, 0),
    "A-PLANT": (3, 13), "A-TEXT": (7, 18), "A-SECTION": (1, 25), "A-DIM": (7, 13),
}
for name, (color, lw) in LAYERS.items():
    doc.layers.add(name, color=color, lineweight=lw)
doc.styles.add("ARCH", font="arial.ttf")
EXT, INT, SITE = 0.30, 0.15, 0.25

# ------------------------------------------------------------------ walls (pixel coordinates read off the sketch)
walls_px = [
    # exterior
    (382, 325, 1090, 325, EXT),    # north wall
    (382, 325, 382, 555, EXT),     # west wall (bath + majlis)
    (382, 555, 607, 555, EXT),     # majlis south wall (porch side)
    (488, 555, 488, 800, EXT),     # entrance wall porch | hall
    (385, 800, 488, 800, EXT),     # living north wall (porch side)
    (385, 800, 385, 990, EXT),     # living west wall
    (385, 990, 905, 990, EXT),     # living + dining south wall
    (820, 800, 905, 925, EXT),     # diagonal dining wall facing the garden
    (905, 917, 905, 1103, EXT),    # kitchen west wall
    (905, 917, 1203, 917, EXT),    # kitchen + laundry north wall
    (1090, 325, 1090, 800, EXT),   # east wall
    (908, 800, 1090, 800, EXT),    # kids 2 block south wall
    # interior
    (382, 395, 607, 395, INT),     # bath | majlis
    (500, 325, 500, 392, INT),     # WC partition
    (607, 325, 607, 555, INT),     # majlis east wall
    (678, 325, 678, 442, INT),     # bath 2 | kids 1
    (607, 442, 678, 442, INT),     # bath 2 south wall
    (797, 325, 797, 517, INT),     # kids 1 | master
    (607, 517, 1003, 517, INT),    # corridor north wall
    (942, 325, 942, 420, INT),     # master | master bath
    (942, 410, 1090, 410, INT),    # master bath south wall
    (1003, 410, 1003, 600, INT),   # office west wall
    (908, 600, 1090, 600, INT),    # kids 2 north wall / office south wall
    (605, 648, 908, 648, INT),     # courtyard north (stairs side)
    (605, 648, 605, 800, INT),     # courtyard west (hall side)
    (605, 800, 820, 800, INT),     # courtyard south (living side)
    (908, 600, 908, 800, INT),     # courtyard east | kids 2
    (972, 733, 1090, 733, INT),    # bath 3 north wall
    (972, 733, 972, 800, INT),     # bath 3 west wall
    (1083, 917, 1083, 1103, INT),  # kitchen | laundry
]

# doors: (kind, hinge_px, closed_end_px, swing)   swing = side the open leaf lies on (N = up on the sheet)
doors_px = [
    ("double", (488, 628), (488, 712), "E"),    # 1  main entrance, porch -> hall
    ("single", (412, 555), (455, 555), "N"),    # 2  majlis, from the porch
    ("single", (500, 392), (500, 350), "W"),    # 3  WC in the guest bath
    ("single", (672, 442), (637, 442), "N"),    # 4  bath 2, from kids 1
    ("single", (790, 517), (747, 517), "N"),    # 5  kids 1
    ("single", (810, 517), (852, 517), "N"),    # 6  master
    ("single", (990, 410), (948, 410), "N"),    # 7  master bath
    ("single", (1003, 580), (1003, 540), "E"),  # 8  office
    ("single", (915, 600), (960, 600), "S"),    # 9  kids 2
    ("single", (972, 770), (972, 738), "E"),    # 10 bath 3
    ("single", (905, 932), (905, 970), "E"),    # 11 kitchen, from dining
    ("single", (1197, 917), (1150, 917), "S"),  # 12 laundry, from the garden
]
openings_px = [((530, 395), (578, 395))]                     # open doorway majlis -> wash basins
windows_px = [((467, 990), (583, 990), EXT), ((702, 990), (845, 990), EXT),   # living / dining
              ((705, 648), (840, 648), INT),                                  # courtyard glazing
              # windows marked in green on the reviewed print
              ((425, 325), (485, 325), EXT),     # guest bath (WC) north
              ((625, 325), (665, 325), EXT),     # bath 2 north
              ((700, 325), (785, 325), EXT),     # kids 1 north
              ((840, 325), (915, 325), EXT),     # master north
              ((995, 325), (1050, 325), EXT),    # master bath north
              ((382, 420), (382, 520), EXT),     # majlis west
              ((1090, 440), (1090, 550), EXT),   # office east
              ((385, 820), (385, 970), EXT),     # living room west
              ((1020, 800), (1065, 800), EXT),   # bath 3 south
              ]
site_windows_px = [((960, 1103), (1040, 1103)),   # kitchen south (in the boundary wall line)
                   ((1120, 1103), (1190, 1103))]  # laundry south
# sliding doors marked in red on the reviewed print: (end_a, end_b, wall thickness)
sliding_px = [((725, 800), (810, 800), INT),      # living | courtyard
              ((965, 917), (1050, 917), EXT)]     # kitchen | garden

NRM = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}


def seg_poly(a, b, t):
    return LineString([a, b]).buffer(t / 2, cap_style="square", join_style="mitre")


def cut(a, b, depth=0.8):
    (x1, y1), (x2, y2) = a, b
    if abs(y1 - y2) < 1e-6:
        return box(min(x1, x2), y1 - depth / 2, max(x1, x2), y1 + depth / 2)
    return box(x1 - depth / 2, min(y1, y2), x1 + depth / 2, max(y1, y2))


walls = [(P(x1, y1), P(x2, y2), t) for x1, y1, x2, y2, t in walls_px]
doors = [(k, P(*h), P(*c), s) for k, h, c, s in doors_px]
openings = [(P(*a), P(*b)) for a, b in openings_px]
windows = [(P(*a), P(*b), t) for a, b, t in windows_px]
site_windows = [(P(*a), P(*b), SITE) for a, b in site_windows_px]
sliding = [(P(*a), P(*b), t) for a, b, t in sliding_px]

solid = unary_union([seg_poly(a, b, t) for a, b, t in walls])
solid = solid.difference(unary_union(
    [cut(h, c) for _, h, c, _ in doors] + [cut(a, b) for a, b in openings] + [cut(a, b) for a, b, _ in windows]
    + [cut(a, b) for a, b, _ in sliding]))


def add_filled(geom, layer, hatch_layer, color=8):
    for p in ([geom] if isinstance(geom, Polygon) else list(geom.geoms)):
        msp.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={"layer": layer})
        for hole in p.interiors:
            msp.add_lwpolyline(list(hole.coords), close=True, dxfattribs={"layer": layer})
        h = msp.add_hatch(color=color, dxfattribs={"layer": hatch_layer})
        h.paths.add_polyline_path(list(p.exterior.coords)[:-1], is_closed=True, flags=1)
        for hole in p.interiors:
            h.paths.add_polyline_path(list(hole.coords)[:-1], is_closed=True, flags=0)


add_filled(solid, "A-WALL", "A-WALL-HATCH")

# ------------------------------------------------------------------ plot wall + gates
gate_ped = (P(185, 410), P(185, 492))
gate_car = (P(187, 730), P(187, 928))
site = LineString([P(PX0, PY1), P(PX1, PY1), P(PX1, PY0), P(PX0, PY0), P(PX0, PY1)]).buffer(
    SITE / 2, join_style="mitre")
site = site.difference(cut(*gate_ped)).difference(cut(*gate_car))
site = site.difference(unary_union([cut(a, b) for a, b, _ in site_windows]))
add_filled(site, "A-SITE-WALL", "A-WALL-HATCH")
# sliding car-gate leaf, just inside the wall (x 208..218, y 747..942 on the sketch)
a, b = P(208, 942), P(218, 747)
msp.add_lwpolyline([a, (b[0], a[1]), b, (a[0], b[1])], close=True, dxfattribs={"layer": "A-DOOR"})

# ------------------------------------------------------------------ door symbols
DL = {"layer": "A-DOOR"}


def ang(v):
    return math.degrees(math.atan2(v[1], v[0])) % 360


def leaf(h, c, swing):
    w = math.dist(h, c)
    n = NRM[swing]
    msp.add_line(h, (h[0] + n[0] * w, h[1] + n[1] * w), dxfattribs=DL)
    a_n, a_c = ang(n), ang((c[0] - h[0], c[1] - h[1]))
    start, end = (a_n, a_c) if round((a_c - a_n) % 360) == 90 else (a_c, a_n)
    msp.add_arc(h, w, start, end, dxfattribs=DL)


for kind, h, c, s in doors:
    if kind == "single":
        leaf(h, c, s)
    else:
        mid = ((h[0] + c[0]) / 2, (h[1] + c[1]) / 2)
        leaf(h, mid, s)
        leaf(c, mid, s)
leaf(gate_ped[0], gate_ped[1], "E")      # entrance gate swings into the plot

WN = {"layer": "A-WINDOW"}
for a, b, t in windows + site_windows:
    horiz = abs(a[1] - b[1]) < 1e-6
    for off in (-t / 2, -0.03, 0.03, t / 2):                 # wall faces + double glass line
        if horiz:
            msp.add_line((a[0], a[1] + off), (b[0], b[1] + off), dxfattribs=WN)
        else:
            msp.add_line((a[0] + off, a[1]), (b[0] + off, b[1]), dxfattribs=WN)
    for e in (a, b):                                          # jambs
        if horiz:
            msp.add_line((e[0], e[1] - t / 2), (e[0], e[1] + t / 2), dxfattribs=WN)
        else:
            msp.add_line((e[0] - t / 2, e[1]), (e[0] + t / 2, e[1]), dxfattribs=WN)

# sliding doors: two overlapping glazed panels on parallel tracks + jambs + arrows
for a, b, t in sliding:
    (x0, y0), (x1, y1) = a, b
    w = abs(x1 - x0)
    pw = w * 0.55
    xs = min(x0, x1)
    for e in (x0, x1):
        msp.add_line((e, y0 - t / 2), (e, y0 + t / 2), dxfattribs=DL)
    for px, off in ((xs, 0.035), (xs + w - pw, -0.035)):
        pts = [(px, y0 + off - 0.02), (px + pw, y0 + off - 0.02), (px + pw, y0 + off + 0.02), (px, y0 + off + 0.02)]
        msp.add_lwpolyline(pts, close=True, dxfattribs=DL)
    yy = y0 + t / 2 + 0.12
    msp.add_line((xs + w * 0.3, yy), (xs + w * 0.7, yy), dxfattribs=DL)
    msp.add_lwpolyline([(xs + w * 0.7 - 0.1, yy + 0.05), (xs + w * 0.7, yy), (xs + w * 0.7 - 0.1, yy - 0.05)], dxfattribs=DL)

# ------------------------------------------------------------------ stairs (x 607..905, y 602..646 on the sketch)
# straight flight between corridor and courtyard: 27 treads of ~0.28 m, handrails, walking line,
# UP arrow and break line; treads beyond the break are dashed (upper part of the flight).
ST = {"layer": "A-STAIR"}
SX0, SX1, SY0, SY1 = 607, 905, 602, 646
n_tr = 27
step = (SX1 - SX0) / n_tr
x_break = 772
msp.add_lwpolyline([P(SX0, SY0), P(SX1, SY0), P(SX1, SY1), P(SX0, SY1)], close=True, dxfattribs=ST)   # stringers
for yy in (SY0 + 2.5, SY1 - 2.5):                                                                      # handrails
    msp.add_line(P(SX0, yy), P(SX1, yy), dxfattribs=ST)
for i in range(1, n_tr):
    x = SX0 + i * step
    attrs = dict(ST) if x < x_break else {"layer": "A-STAIR", "linetype": "DASHED", "ltscale": 0.06}
    msp.add_line(P(x, SY0), P(x, SY1), dxfattribs=attrs)
for i in range(1, n_tr + 1):                                                                           # riser numbers
    if SX0 + i * step < x_break - 6:
        x = SX0 + (i - 0.5) * step
        msp.add_text(str(i), height=0.09, dxfattribs={"layer": "A-STAIR", "style": "ARCH"}).set_placement(
            P(x, SY0 + 7), align=TextEntityAlignment.MIDDLE_CENTER)
ym = (SY0 + SY1) / 2
C0 = P(SX0 + step / 2, ym)
msp.add_circle(C0, 0.05, dxfattribs=ST)                                                                # start of walking line
msp.add_lwpolyline([C0, P(SX1 - step / 2, ym)], dxfattribs=ST)
msp.add_lwpolyline([P(SX1 - step / 2 - 9, ym - 5), P(SX1 - step / 2, ym), P(SX1 - step / 2 - 9, ym + 5)], dxfattribs=ST)
msp.add_lwpolyline([P(x_break - 6, SY1), P(x_break - 2, ym + 4), P(x_break + 2, ym - 4), P(x_break + 6, SY0)], dxfattribs=ST)
msp.add_lwpolyline([P(x_break + 2, SY1), P(x_break + 6, ym + 4), P(x_break + 10, ym - 4), P(x_break + 14, SY0)], dxfattribs=ST)

# ------------------------------------------------------------------ drawing helpers (pixel input)
F = "A-FURN"


def poly(geom, layer=F):
    for g in ([geom] if geom.geom_type in ("Polygon", "LineString") else list(geom.geoms)):
        if g.geom_type == "Polygon":
            msp.add_lwpolyline([P(x, y) for x, y in g.exterior.coords], close=True, dxfattribs={"layer": layer})
        else:
            msp.add_lwpolyline([P(x, y) for x, y in g.coords], dxfattribs={"layer": layer})


def dark(geom, layer=F):
    """dark-shaded item on the sketch (wardrobes, TV unit): outline + hatch."""
    poly(geom, layer)
    h = msp.add_hatch(color=8, dxfattribs={"layer": "A-FURN-HATCH"})
    h.set_pattern_fill("ANSI31", scale=0.03)
    h.paths.add_polyline_path([P(x, y) for x, y in geom.exterior.coords][:-1], is_closed=True)


def rbox(x0, y0, x1, y1, r=0):
    g = box(x0, y0, x1, y1)
    return g.buffer(-r).buffer(r, join_style="round") if r else g


def R(x0, y0, x1, y1, r=0, layer=F):
    poly(rbox(x0, y0, x1, y1, r), layer)


def C(x, y, r, layer=F):
    msp.add_circle(P(x, y), L(r), dxfattribs={"layer": layer})


def E(x, y, rx, ry, layer=F):
    if rx >= ry:
        msp.add_ellipse(P(x, y), major_axis=(L(rx), 0), ratio=ry / rx, dxfattribs={"layer": layer})
    else:
        msp.add_ellipse(P(x, y), major_axis=(0, L(ry)), ratio=rx / ry, dxfattribs={"layer": layer})


def Ln(pts, layer=F):
    msp.add_lwpolyline([P(x, y) for x, y in pts], dxfattribs={"layer": layer})


def band(cx, cy, r_out, r_in, a0, a1, layer=F):
    """curved sofa: ring sector between a0..a1 degrees (sheet coords, y down, clockwise)."""
    def pt(r, a):
        return cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
    n = 24
    outer = [pt(r_out, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    inner = [pt(r_in, a1 - (a1 - a0) * i / n) for i in range(n + 1)]
    poly(Polygon(outer + inner), layer)
    for k in range(1, 4):                       # seat cushion joints
        a = a0 + (a1 - a0) * k / 4
        Ln([pt(r_in, a), pt(r_out, a)], layer)


def wc(x, y, facing):
    """tank against the wall at (x, y); bowl towards `facing` (N/S/E/W on the sheet)."""
    if facing in "NS":
        d = 1 if facing == "S" else -1
        R(x - 9, y - 4, x + 9, y + 4, 2); E(x, y + d * 13, 7, 10)
    else:
        d = 1 if facing == "E" else -1
        R(x - 4, y - 9, x + 4, y + 9, 2); E(x + d * 13, y, 10, 7)


def basin(x, y, rx=10, ry=None):
    ry = ry or rx
    E(x, y, rx, ry); E(x, y, rx * 0.55, ry * 0.55)


def tree(x, y, r, spikes=14):
    pts = []
    for k in range(spikes * 2):
        a = math.pi * k / spikes
        rr = r if k % 2 == 0 else r * 0.62
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    poly(Polygon(pts), "A-PLANT")
    for k in range(spikes):
        a = 2 * math.pi * k / spikes
        Ln([(x, y), (x + r * 0.85 * math.cos(a), y + r * 0.85 * math.sin(a))], "A-PLANT")
    C(x, y, r * 0.12, "A-PLANT")


def palm(x, y, r):
    for a in (150, 175, 200, 225, 250, 280, 310, 120):
        rad = math.radians(a)
        tip = (x + r * math.cos(rad), y + r * math.sin(rad))
        mid = (x + r * 0.5 * math.cos(rad), y + r * 0.5 * math.sin(rad))
        nx, ny = -math.sin(rad) * r * 0.12, math.cos(rad) * r * 0.12
        poly(Polygon([(x, y), (mid[0] + nx, mid[1] + ny), tip, (mid[0] - nx, mid[1] - ny)]), "A-PLANT")


def stones(region, avoid, seed, n_try=1500, gap=17):
    rnd = random.Random(seed)
    minx, miny, maxx, maxy = region.bounds
    placed = []
    for _ in range(n_try):
        x, y = rnd.uniform(minx, maxx), rnd.uniform(miny, maxy)
        pt = Point(x, y)
        if region.contains(pt.buffer(8)) and not avoid.intersects(pt.buffer(8)) and \
                all(pt.distance(q) > gap for q in placed):
            placed.append(pt)
            g = affinity.rotate(affinity.scale(Point(x, y).buffer(1, 12), rnd.uniform(6, 9), rnd.uniform(4.5, 6.5)),
                                rnd.uniform(0, 180))
            poly(g, "A-PLANT")


# ------------------------------------------------------------------ furniture & fittings (sketch positions)
# guest bath: WC compartment (x 382..500) + wash area (x 500..607)
wc(415, 333, "S"); basin(455, 340, 10)
Ln([(500, 350), (607, 350)])                            # vanity counter edge
basin(535, 338, 11, 8); basin(570, 338, 11, 8)
# majlis
C(407, 412, 9)                                          # round side table
band(495, 478, 72, 58, 198, 290)                        # curved sofa (north-west)
R(393, 448, 432, 490, 6)                                # armchair
R(455, 440, 537, 512)                                   # majlis table / rug
dark(box(570, 418, 600, 500))                           # TV unit
band(527, 497, 50, 36, 30, 145)                         # curved sofa (south)
# bath 2
R(612, 326, 650, 366); Ln([(612, 366), (650, 326)]); Ln([(620, 330), (630, 350)]); Ln([(632, 330), (640, 352)])
basin(632, 385, 9, 7); wc(615, 420, "E")
# kids 1
R(718, 335, 770, 440, 5); R(725, 340, 763, 356, 4); Ln([(718, 365), (770, 365)]); Ln([(735, 365), (765, 420)])
dark(box(612, 448, 640, 512)); dark(box(640, 490, 685, 512))   # wardrobe + cabinet
# master
R(832, 335, 908, 440, 5); R(838, 340, 868, 356, 4); R(872, 340, 902, 356, 4); Ln([(832, 365), (908, 365)])
R(808, 333, 830, 350, 3); R(910, 333, 932, 350, 3)      # bedside tables
dark(box(932, 485, 990, 515))                           # built-in wardrobe
# master bath
Ln([(948, 360), (1048, 360)])                           # vanity counter edge
basin(975, 340, 11, 7); wc(1020, 333, "S")
R(1053, 333, 1082, 402, 6); R(1058, 340, 1077, 396, 8)   # bathtub
# office: L-shaped desk + chair
poly(Polygon([(1010, 435), (1060, 435), (1060, 515), (1048, 515), (1048, 447), (1010, 447)]))
C(1037, 462, 11)
# kids 2
R(978, 648, 1080, 698, 5); R(1052, 655, 1074, 691, 4); Ln([(1040, 648), (1040, 698)]); Ln([(985, 690), (1035, 655)])
dark(Polygon([(910, 725), (940, 725), (940, 772), (972, 772), (972, 800), (910, 800)]))   # wardrobe (L)
# bath 3
wc(1023, 750, "S"); basin(992, 791, 8, 7)
R(1045, 762, 1080, 797); Ln([(1045, 797), (1080, 762)]); Ln([(1055, 770), (1065, 790)])
# living room
poly(Polygon([(398, 905), (398, 830), (402, 820), (412, 813), (500, 813), (500, 845), (440, 845),
              (432, 850), (430, 905)]))                 # L-sofa (west + north)
for x in (440, 470):
    Ln([(x, 813), (x, 845)])
Ln([(398, 870), (430, 870)])
C(423, 888, 14)                                         # round seat
E(522, 887, 78, 48)                                     # oval rug / table
C(473, 930, 11)                                         # black side table
poly(affinity.rotate(rbox(422, 925, 458, 961, 4), 35))  # armchair (angled)
R(495, 943, 535, 978, 5)                                # armchair
poly(Polygon([(540, 978), (655, 978), (655, 878), (612, 878), (612, 942), (540, 942)]))   # L-sofa (south + east)
for x in (570, 595):
    Ln([(x, 942), (x, 978)])
C(632, 898, 14)                                         # round seat
C(622, 818, 10)                                         # plant pot
# dining: table for 8
R(725, 878, 808, 925, 14)
for x in (743, 763, 788):
    R(x - 8, 855, x + 8, 872, 4)
for x in (746, 766, 790):
    R(x - 8, 930, x + 8, 947, 4)
R(707, 890, 719, 912, 4); R(814, 890, 826, 912, 4)
# kitchen
R(912, 935, 935, 1098)                                  # counter along west wall
R(915, 990, 932, 1022)                                  # sink
for bx, by in ((918, 1033), (929, 1033), (918, 1048), (929, 1048)):
    C(bx, by, 4)                                        # hob
R(935, 1080, 1052, 1098)                                # counter along south wall
basin(972, 1089, 10, 6)
R(1052, 925, 1078, 1098)                                # counter along east wall
R(978, 978, 1012, 1045)                                 # island
# laundry
R(1090, 925, 1108, 1080); Ln([(1090, 1000), (1108, 1000)]); Ln([(1090, 1040), (1108, 1040)])
R(1112, 1080, 1145, 1098); R(1150, 1080, 1185, 1098)
# porch: walkway lines + two planters
Ln([(383, 560), (383, 795)]); Ln([(410, 560), (410, 795)])
C(398, 787, 8); C(420, 787, 8)
# car
R(280, 868, 345, 1045, 14); R(290, 912, 335, 960, 8); Ln([(287, 900), (338, 900)])
Ln([(287, 1000), (338, 1000)]); R(294, 1005, 331, 1035, 6)

# courtyard: fountain, planter, bench, trees, pebbles
for r in (50, 35, 10):
    C(698, 738, r, "A-PLANT")
E(630, 748, 20, 42, "A-PLANT")                          # planter (west)
R(882, 700, 900, 785, 8, "A-PLANT")                     # bench (east)
cx, cy, rr = 825, 612, 117                              # curved planter edge
arc_pts = [(cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))) for a in range(40, 141, 4)]
Ln([p for p in arc_pts if 612 < p[0] < 905 and p[1] > 652], "A-PLANT")
for x, y, r in ((640, 682, 22), (765, 672, 28), (815, 690, 25), (865, 675, 25)):
    tree(x, y, r)
court = box(612, 655, 900, 795)
court_avoid = unary_union([Point(698, 738).buffer(54), Point(cx, cy).buffer(rr + 4),
                           affinity.scale(Point(630, 748).buffer(1), 24, 46), box(876, 695, 905, 790),
                           Point(640, 682).buffer(24)])
stones(court, court_avoid, seed=3)
# garden between courtyard, kids 2 and kitchen (pebbles + two trees)
garden = Polygon([(828, 805), (1198, 805), (1198, 912), (910, 912)])
for x, y, r in ((965, 825, 26), (1025, 825, 25)):
    tree(x, y, r)
stones(garden, unary_union([Point(965, 825).buffer(28), Point(1025, 825).buffer(27)]), seed=11)
# timber deck east of kids 2
for y in (607, 727, 744, 761, 778, 795):
    Ln([(1095, y), (1198, y)], "A-PLANT")
# landscape trees
for x, y, r in ((235, 297, 37), (305, 278, 30), (665, 1065, 28), (725, 1050, 32), (875, 1030, 28)):
    tree(x, y, r)
palm(835, 1078, 70)


# ------------------------------------------------------------------ text (names & sizes as written on the sketch)
def T(x, y, s, h=0.3, rot=0, layer="A-TEXT", align=TextEntityAlignment.MIDDLE_CENTER):
    msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "ARCH"}).set_placement(
        P(x, y), align=align)


for x, y, name, size, h in [
    (497, 470, "MAJLIS", "6 x 4 m", 0.3), (420, 372, "BATH", "", 0.2), (553, 375, "WASH", "", 0.16),
    (655, 400, "BATH", "", 0.16), (745, 468, "KIDS 1", "3 x 5 m", 0.26), (870, 468, "MASTER", "3.5 x 5 m", 0.26),
    (1030, 385, "BATH", "", 0.2), (1032, 530, "OFFICE", "", 0.2), (945, 665, "KIDS 2", "3 x 5 m", 0.24),
    (1000, 745, "BATH", "", 0.14), (700, 560, "CORRIDOR", "", 0.24), (548, 700, "HALL", "", 0.24),
    (760, 785, "COURTYARD", "", 0.2), (522, 880, "LIVING ROOM", "8 x 5 m", 0.26), (766, 897, "DINING", "4 x 3 m", 0.18),
    (995, 955, "KITCHEN", "4.5 x 5 m", 0.22), (1145, 990, "LAUNDRY", "", 0.2), (440, 615, "PORCH", "", 0.22),
    (312, 830, "PARKING", "", 0.24), (1110, 870, "GARDEN", "", 0.24),
]:
    T(x, y, name, h)
    if size:
        T(x, y + h / SY * 1.35, size, h * 0.75)
T(1128, 1089, "WM", 0.13); T(1167, 1089, "DR", 0.13)
T(358, 702, "+0.00", 0.2, rot=-90); T(432, 722, "+0.15", 0.2, rot=-90)
T(630, 637, "UP", 0.16)
T(30, 438, "ENTRANCE", 0.3, align=TextEntityAlignment.MIDDLE_LEFT)
Ln([(130, 438), (175, 438)], "A-TEXT"); Ln([(165, 432), (175, 438), (165, 444)], "A-TEXT")
T(530, 115, "FLOOR PLAN", 1.0)
C(548, 1135, 6, "A-TEXT")
T(600, 1130, "FLOOR PLAN", 0.32); T(600, 1148, "SCALE 1:100", 0.22)
Ln([(560, 1139), (660, 1139)], "A-TEXT")


# ------------------------------------------------------------------ section lines A-A and B-B
def section(a, b, name, tick):
    msp.add_line(P(*a), P(*b), dxfattribs={"layer": "A-SECTION", "linetype": "DASHDOT"})
    for e in (a, b):
        msp.add_line(P(*e), P(e[0] + tick[0], e[1] + tick[1]), dxfattribs={"layer": "A-SECTION"})
        T(e[0] + tick[0] * 1.8, e[1] + tick[1] * 1.8, name, 0.4, layer="A-SECTION")


section((110, 615), (1265, 615), "A", (0, -22))
section((942, 165), (942, 1160), "B", (22, 0))

# ------------------------------------------------------------------ overall dimensions (metres)
DIMOV = {"dimlfac": 1, "dimdec": 2, "dimtxt": 0.3, "dimasz": 0.25, "dimexo": 0.1, "dimexe": 0.2, "dimgap": 0.08}
DA = {"layer": "A-DIM"}
hx0, hy1 = P(382, 325)
hx1, _ = P(1090, 325)
msp.add_linear_dim(base=(0, PLOT_H + 2.0), p1=(0, PLOT_H), p2=(PLOT_W, PLOT_H), dxfattribs=DA, override=DIMOV).render()
msp.add_linear_dim(base=(PLOT_W + 2.4, 0), p1=(PLOT_W, 0), p2=(PLOT_W, PLOT_H), angle=90, dxfattribs=DA, override=DIMOV).render()
msp.add_linear_dim(base=(0, PLOT_H - 0.9), p1=(hx0, hy1), p2=(hx1, hy1), dxfattribs=DA, override=DIMOV).render()

doc.saveas(OUT)
print("saved", OUT)

# ------------------------------------------------------------------ preview PNG
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy

    fig = plt.figure(figsize=(16, 15))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp)
    fig.savefig(OUT.with_name("floor_plan_preview.png"), dpi=120)
    print("preview saved")
except Exception as e:
    print("preview skipped:", e)
