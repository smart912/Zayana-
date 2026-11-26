"""Hand-drawn FLOOR PLAN (scale 1:100) traced into an AutoCAD DXF.

Every wall, door, window and piece of furniture is placed at the exact position
measured on the original sketch (pixel coordinates of the photo), then converted
with ONE uniform scale so the plot is 26.00 m x 22.00 m.  Nothing is moved or
re-arranged - the layout is the same as the drawing.

Units: metres (1 drawing unit = 1 m).  Origin = bottom-left corner of the plot.
Run:  python3 floor_plan.py   ->  floor_plan.dxf  (+ floor_plan_preview.png)
"""
import math
import random
from pathlib import Path

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union

OUT = Path(__file__).with_name("floor_plan.dxf")

# ------------------------------------------------------------------ sketch -> metres
# plot wall on the photo: x 190..1210 px, y 245..1105 px  ->  26 m x 22 m
PX0, PX1, PY0, PY1 = 190, 1210, 245, 1105
PLOT_W, PLOT_H = 26.0, 22.0
SX, SY = PLOT_W / (PX1 - PX0), PLOT_H / (PY1 - PY0)   # ~0.0255 m per pixel both ways


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
    "A-WINDOW": (4, 18), "A-STAIR": (2, 18), "A-FURN": (9, 13), "A-PLANT": (3, 13),
    "A-TEXT": (7, 18), "A-SECTION": (1, 25), "A-DIM": (7, 13),
}
for name, (color, lw) in LAYERS.items():
    doc.layers.add(name, color=color, lineweight=lw)
doc.styles.add("ARCH", font="arial.ttf")
EXT, INT, SITE = 0.30, 0.15, 0.25

# ------------------------------------------------------------------ walls (pixel coords from the sketch)
walls_px = [
    # exterior
    (382, 323, 1095, 323, EXT),   # north wall
    (382, 323, 382, 550, EXT),    # west wall: bath + majlis
    (382, 550, 607, 550, EXT),    # majlis south wall (porch side)
    (490, 550, 490, 800, EXT),    # entrance wall: porch -> hall
    (385, 800, 490, 800, EXT),    # living north wall (porch side)
    (385, 800, 385, 990, EXT),    # living west wall
    (385, 990, 905, 990, EXT),    # living + dining south wall
    (905, 910, 905, 1105, EXT),   # dining east / kitchen west wall
    (820, 800, 905, 910, EXT),    # diagonal dining wall to garden
    (905, 913, 1210, 913, EXT),   # kitchen + laundry north wall
    (1095, 323, 1095, 800, EXT),  # east wall
    (905, 800, 1095, 800, EXT),   # kids 2 block south wall
    # interior
    (382, 395, 607, 395, INT),    # bath / majlis
    (497, 323, 497, 392, INT),    # WC partition
    (607, 323, 607, 550, INT),    # majlis east wall
    (677, 323, 677, 445, INT),    # bath 2 / kids 1
    (607, 445, 677, 445, INT),    # bath 2 south wall
    (797, 323, 797, 517, INT),    # kids 1 / master
    (607, 517, 1000, 517, INT),   # corridor north wall
    (942, 323, 942, 420, INT),    # master / master bath
    (942, 405, 1095, 405, INT),   # master bath south wall
    (1000, 405, 1000, 600, INT),  # office west wall
    (905, 600, 1095, 600, INT),   # kids 2 north wall / office south wall
    (605, 648, 905, 648, INT),    # courtyard north (stairs side)
    (605, 648, 605, 800, INT),    # courtyard west (hall side)
    (605, 800, 820, 800, INT),    # courtyard south (living side)
    (905, 600, 905, 800, INT),    # courtyard east / kids 2 west
    (975, 733, 1095, 733, INT),   # bath 3 north wall
    (975, 733, 975, 800, INT),    # bath 3 west wall
    (1080, 913, 1080, 1105, INT), # kitchen / laundry
]

# doors: (hinge_px, closed_end_px, swing)  swing = side the leaf opens to: N/S/E/W (N = up on the sheet)
doors_px = [
    ("double", (490, 625), (490, 712), "E"),   # main entrance porch -> hall (two leaves)
    ("single", (412, 550), (455, 550), "N"),   # majlis (from porch)
    ("single", (497, 392), (497, 350), "W"),   # WC in guest bath
    ("single", (672, 445), (630, 445), "N"),   # bath 2 (from kids 1)
    ("single", (787, 517), (745, 517), "N"),   # kids 1
    ("single", (812, 517), (852, 517), "N"),   # master
    ("single", (985, 405), (950, 405), "N"),   # master bath
    ("single", (1000, 590), (1000, 543), "E"), # office
    ("single", (915, 600), (960, 600), "S"),   # kids 2
    ("single", (975, 772), (975, 733), "E"),   # bath 3
    ("single", (905, 978), (905, 928), "E"),   # kitchen (from dining)
    ("single", (1200, 913), (1152, 913), "S"), # laundry (from garden)
]
openings_px = [((520, 395), (600, 395))]       # open arch majlis -> wash basins
windows_px = [((700, 990), (890, 990), EXT)]    # glazed strip, living/dining south wall

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

solid = unary_union([seg_poly(a, b, t) for a, b, t in walls])
solid = solid.difference(unary_union(
    [cut(h, c) for _, h, c, _ in doors] + [cut(a, b) for a, b in openings] + [cut(a, b) for a, b, _ in windows]))


def add_filled(geom, layer, hatch_layer):
    for p in ([geom] if isinstance(geom, Polygon) else list(geom.geoms)):
        msp.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={"layer": layer})
        for hole in p.interiors:
            msp.add_lwpolyline(list(hole.coords), close=True, dxfattribs={"layer": layer})
        h = msp.add_hatch(color=8, dxfattribs={"layer": hatch_layer})
        h.paths.add_polyline_path(list(p.exterior.coords)[:-1], is_closed=True, flags=1)
        for hole in p.interiors:
            h.paths.add_polyline_path(list(hole.coords)[:-1], is_closed=True, flags=0)


add_filled(solid, "A-WALL", "A-WALL-HATCH")

# ------------------------------------------------------------------ plot (site) wall with the two gates
gate_ped = (P(190, 410), P(190, 490))
gate_car = (P(190, 730), P(190, 935))
site = LineString([P(PX0, PY1), P(PX1, PY1), P(PX1, PY0), P(PX0, PY0), P(PX0, PY1)]).buffer(
    SITE / 2, join_style="mitre")
site = site.difference(cut(*gate_ped)).difference(cut(*gate_car))
for p in (site.geoms if hasattr(site, "geoms") else [site]):
    msp.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={"layer": "A-SITE-WALL"})
# sliding car gate leaf (drawn just inside the wall like the sketch)
gx0, gy0 = P(209, 940)
gx1, gy1 = P(217, 745)
msp.add_lwpolyline([(gx0, gy0), (gx1, gy0), (gx1, gy1), (gx0, gy1)], close=True,
                   dxfattribs={"layer": "A-DOOR"})

# ------------------------------------------------------------------ door symbols
DL = {"layer": "A-DOOR"}


def ang(v):
    return math.degrees(math.atan2(v[1], v[0])) % 360


def leaf(h, c, swing):
    w = math.dist(h, c)
    n = NRM[swing]
    tip = (h[0] + n[0] * w, h[1] + n[1] * w)
    msp.add_line(h, tip, dxfattribs=DL)
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
leaf(gate_ped[0], gate_ped[1], "E")          # pedestrian gate swings into the plot

for a, b, t in windows:
    for off in (-t / 2, -0.03, 0.03, t / 2):
        msp.add_line((a[0], a[1] + off), (b[0], b[1] + off), dxfattribs={"layer": "A-WINDOW"})
    for e in (a, b):
        msp.add_line((e[0], e[1] - t / 2), (e[0], e[1] + t / 2), dxfattribs={"layer": "A-WINDOW"})

# ------------------------------------------------------------------ stairs (x 605..905, y 600..648 px)
ST = {"layer": "A-STAIR"}
for i in range(23):
    x = 612 + i * 13
    msp.add_line(P(x, 602), P(x, 646), dxfattribs=ST)
msp.add_lwpolyline([P(605, 618), P(665, 618)], dxfattribs=ST)
msp.add_lwpolyline([P(655, 612), P(665, 618), P(655, 624)], dxfattribs=ST)
msp.add_lwpolyline([P(742, 646), P(752, 624), P(760, 628), P(770, 602)], dxfattribs=ST)   # break line


# ------------------------------------------------------------------ furniture (all at sketch positions)
F = {"layer": "A-FURN"}


def R(x0, y0, x1, y1, layer="A-FURN"):
    a, b = P(x0, y1), P(x1, y0)
    msp.add_lwpolyline([a, (b[0], a[1]), b, (a[0], b[1])], close=True, dxfattribs={"layer": layer})


def C(x, y, r, layer="A-FURN"):
    msp.add_circle(P(x, y), L(r), dxfattribs={"layer": layer})


def E(x, y, rx, ry, layer="A-FURN"):
    if rx >= ry:
        msp.add_ellipse(P(x, y), major_axis=(L(rx), 0), ratio=ry / rx, dxfattribs={"layer": layer})
    else:
        msp.add_ellipse(P(x, y), major_axis=(0, L(ry)), ratio=rx / ry, dxfattribs={"layer": layer})


def Ln(x0, y0, x1, y1, layer="A-FURN"):
    msp.add_line(P(x0, y0), P(x1, y1), dxfattribs={"layer": layer})


def X(x0, y0, x1, y1):  # box with cross (shower)
    R(x0, y0, x1, y1); Ln(x0, y0, x1, y1); Ln(x0, y1, x1, y0)


def bed(x0, y0, x1, y1, pillow):
    R(x0, y0, x1, y1)
    if pillow == "N":
        if x1 - x0 > 50:
            R(x0 + 4, y0 + 4, (x0 + x1) / 2 - 2, y0 + 18); R((x0 + x1) / 2 + 2, y0 + 4, x1 - 4, y0 + 18)
        else:
            R(x0 + 5, y0 + 4, x1 - 5, y0 + 18)
        Ln(x0, y0 + (y1 - y0) * 0.45, x1, y0 + (y1 - y0) * 0.45)
    else:  # pillow on east side
        R(x1 - 20, y0 + 5, x1 - 5, y1 - 5)
        Ln(x0 + (x1 - x0) * 0.55, y0, x0 + (x1 - x0) * 0.55, y1)


def wc(x, y, facing):  # tank against the wall, bowl towards `facing` (on the sheet)
    dx, dy = {"S": (0, 1), "N": (0, -1), "E": (1, 0), "W": (-1, 0)}[facing]
    if dy:
        R(x - 9, y - 4, x + 9, y + 4); E(x, y + dy * 13, 7, 10)
    else:
        R(x - 4, y - 9, x + 4, y + 9); E(x + dx * 13, y, 10, 7)


def basin(x, y, r=10):
    C(x, y, r); C(x, y, r * 0.45)


def tree(x, y, r):
    C(x, y, r, "A-PLANT"); C(x, y, r * 0.15, "A-PLANT")
    for k in range(12):
        a = math.radians(k * 30)
        Ln(x, y, x + r * math.cos(a), y + r * math.sin(a), "A-PLANT")


# guest bath (WC + wash area)
wc(412, 330, "S"); basin(455, 340, 9); basin(535, 340); basin(580, 340)
R(510, 326, 600, 356)                                  # vanity counter
# majlis
C(407, 412, 9)                                         # side table
R(420, 405, 525, 432)                                  # sofa north
R(390, 440, 432, 485)                                  # armchair west
R(455, 425, 540, 515)                                  # table / rug
R(567, 417, 600, 495)                                  # TV unit
R(485, 500, 575, 543)                                  # sofa south
# bath 2
X(610, 326, 650, 366); basin(630, 385, 8); wc(612, 418, "E")
# kids 1
bed(717, 330, 770, 440, "N"); R(610, 455, 650, 512)    # bed + wardrobe
# master
bed(830, 330, 900, 435, "N"); R(808, 330, 826, 346); R(904, 330, 922, 346)
R(945, 485, 985, 505)                                  # built-in wardrobe (dressing)
# master bath
basin(972, 342, 11); wc(1020, 330, "S"); R(1055, 333, 1082, 400); E(1068, 366, 9, 28)
# office
R(1012, 440, 1075, 515); C(1037, 468, 12)
# kids 2
bed(975, 645, 1080, 700, "E")
R(907, 725, 940, 800); R(940, 772, 975, 800)           # wardrobe (L shape)
# bath 3
basin(992, 788, 8); wc(1025, 795, "N"); X(1042, 760, 1082, 798)
# living room
R(395, 810, 500, 840); R(395, 840, 445, 930)           # L-sofa
R(415, 920, 455, 965)                                  # armchair
E(522, 885, 77, 55)                                    # rug / coffee table
C(472, 930, 10)                                        # side table
R(495, 935, 535, 975)                                  # armchair
R(545, 930, 640, 975); R(600, 880, 655, 930)           # L-sofa south-east
# dining (table for 8)
R(725, 880, 820, 920)
for x in (737, 760, 783, 806):
    R(x - 8, 862, x + 8, 878); R(x - 8, 922, x + 8, 938)
# kitchen
R(907, 990, 935, 1060)                                 # cooktop counter
for bx, by in ((914, 1015), (928, 1015), (914, 1032), (928, 1032)):
    C(bx, by, 4)
R(960, 1080, 1030, 1100); basin(995, 1090, 7)          # sink counter
R(975, 980, 1015, 1045)                                # island
# laundry
R(1115, 1080, 1145, 1100); R(1150, 1080, 1180, 1100)
# porch planters + porch edge
C(395, 785, 8); C(425, 785, 8)
Ln(383, 555, 383, 800)
# car
R(280, 865, 345, 1045); R(288, 925, 337, 975); Ln(285, 905, 340, 905); Ln(285, 1000, 340, 1000)

# courtyard: fountain, planters, trees
for r in (52, 40, 10):
    C(700, 730, r, "A-PLANT")
E(632, 745, 17, 40, "A-PLANT")
R(882, 705, 898, 780, "A-PLANT")
for x, y, r in ((635, 675, 22), (760, 670, 25), (810, 690, 25), (860, 670, 22)):
    tree(x, y, r)
# landscape trees (plot)
for x, y, r in ((235, 295, 35), (305, 268, 25), (665, 1065, 25), (725, 1050, 30), (790, 1060, 40),
                (875, 1025, 25), (960, 822, 28), (1015, 825, 25)):
    tree(x, y, r)
# garden stepping stones (garden strip between courtyard/kids 2 and kitchen)
rnd = random.Random(7)
garden = Polygon([(830, 808), (1205, 808), (1205, 905), (912, 905)])
busy = unary_union([Point(960, 822).buffer(32), Point(1015, 825).buffer(30)])
placed = []
for _ in range(900):
    x, y = rnd.uniform(835, 1200), rnd.uniform(810, 902)
    pt = Point(x, y)
    if garden.contains(pt.buffer(9)) and not busy.intersects(pt.buffer(9)) and all(pt.distance(q) > 19 for q in placed):
        placed.append(pt)
        E(x, y, rnd.uniform(7, 10), rnd.uniform(5, 7), "A-PLANT")
# timber deck east of kids 2
for y in range(612, 800, 18):
    Ln(1100, y, 1205, y, "A-PLANT")


# ------------------------------------------------------------------ text (names & sizes as written on the sketch)
def T(x, y, s, h=0.3, rot=0, layer="A-TEXT", align=TextEntityAlignment.MIDDLE_CENTER):
    msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "ARCH"}).set_placement(
        P(x, y), align=align)


for x, y, name, size, h in [
    (497, 455, "MAJLIS", "6 x 4 m", 0.32), (430, 375, "BATH", "", 0.22), (560, 372, "WASH", "", 0.18),
    (640, 400, "BATH", "", 0.18), (745, 465, "KIDS 1", "3 x 5 m", 0.28), (870, 465, "MASTER", "3.5 x 5 m", 0.28),
    (1030, 380, "BATH", "", 0.22), (1045, 530, "OFFICE", "", 0.22), (950, 670, "KIDS 2", "3 x 5 m", 0.26),
    (1040, 745, "BATH", "", 0.16), (800, 560, "CORRIDOR", "", 0.25), (548, 700, "HALL", "", 0.25),
    (730, 780, "COURTYARD", "", 0.22), (530, 880, "LIVING ROOM", "8 x 5 m", 0.3), (772, 900, "DINING", "4 x 3 m", 0.22),
    (995, 960, "KITCHEN", "4.5 x 5 m", 0.24), (1145, 990, "LAUNDRY", "", 0.22), (440, 610, "PORCH", "", 0.24),
    (312, 830, "PARKING", "", 0.26), (1100, 860, "GARDEN", "", 0.26),
]:
    T(x, y, name, h)
    if size:
        T(x, y + h / SY * 1.35, size, h * 0.75)
T(1130, 1090, "WM", 0.13); T(1165, 1090, "DR", 0.13)
T(335, 690, "+0.00", 0.2, rot=-90); T(420, 715, "+0.15", 0.2, rot=-90)
T(630, 640, "UP", 0.18)
T(30, 438, "ENTRANCE", 0.3, align=TextEntityAlignment.MIDDLE_LEFT)
msp.add_lwpolyline([P(130, 438), P(175, 438)], dxfattribs={"layer": "A-TEXT"})
msp.add_lwpolyline([P(165, 432), P(175, 438), P(165, 444)], dxfattribs={"layer": "A-TEXT"})
T(530, 115, "FLOOR PLAN", 1.0)
T(600, 1135, "FLOOR PLAN", 0.35); T(600, 1153, "SCALE 1:100", 0.25)
Ln(545, 1144, 655, 1144, "A-TEXT")


# ------------------------------------------------------------------ section lines A-A and B-B (as on the sketch)
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
hx0, hy1 = P(382, 323)
hx1, hy0 = P(1095, 990)
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

    fig = plt.figure(figsize=(14, 13))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp)
    fig.savefig(OUT.with_name("floor_plan_preview.png"), dpi=110)
    print("preview saved")
except Exception as e:
    print("preview skipped:", e)
