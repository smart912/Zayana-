"""Convert the hand-drawn FLOOR PLAN (scale 1:100) into an AutoCAD DXF.

Units: metres (1 drawing unit = 1 m). Origin = bottom-left corner of the plot wall.
Dimensions were read from the room labels on the sketch (Majlis 6x4, Living 8x5,
Kids 3x5, Master 3.5x5, Dining 4x3, Kitchen 4.5x5) and the rest scaled to match.

Run:  python3 floor_plan.py   ->  floor_plan.dxf  (+ floor_plan_preview.png)
"""
import math
from pathlib import Path

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString, box, Polygon
from shapely.ops import unary_union

OUT = Path(__file__).with_name("floor_plan.dxf")

doc = ezdxf.new("R2010", setup=True)
doc.units = units.M
doc.header["$INSUNITS"] = 6
doc.header["$MEASUREMENT"] = 1
msp = doc.modelspace()

LAYERS = {
    "A-WALL": (7, 0.50), "A-WALL-HATCH": (8, 0.0), "A-SITE-WALL": (7, 0.35),
    "A-DOOR": (30, 0.18), "A-WINDOW": (4, 0.18), "A-STAIR": (2, 0.18),
    "A-FURN": (9, 0.13), "A-PLANT": (3, 0.13), "A-TEXT": (7, 0.18),
    "A-SECTION": (1, 0.25), "A-AREA": (5, 0.13),
}
for name, (color, lw) in LAYERS.items():
    doc.layers.add(name, color=color, lineweight=int(lw * 100))
doc.styles.add("ARCH", font="arial.ttf")

EXT, INT, SITE = 0.30, 0.15, 0.25

# ---------------------------------------------------------------- walls
# (x1, y1, x2, y2, thickness)
walls = [
    # exterior
    (5.5, 3.2, 5.5, 8.3, EXT), (5.5, 15.0, 5.5, 21.0, EXT),
    (8.3, 8.3, 8.3, 15.0, EXT),                      # entrance wall (porch side)
    (5.5, 21.0, 24.5, 21.0, EXT), (24.5, 21.0, 24.5, 8.3, EXT),
    (24.5, 8.3, 19.5, 8.3, EXT),
    (17.4, 8.3, 19.5, 5.2, EXT),                     # diagonal wall to garden
    (19.5, 5.2, 27.5, 5.2, EXT), (19.5, 0.0, 19.5, 5.2, EXT),
    (19.5, 3.2, 5.5, 3.2, EXT),
    (5.5, 8.3, 8.3, 8.3, EXT), (5.5, 15.0, 8.3, 15.0, EXT),
    # interior
    (8.3, 15.0, 11.5, 15.0, INT), (5.5, 19.0, 11.5, 19.0, INT),
    (11.5, 15.0, 11.5, 21.0, INT), (11.5, 18.0, 13.5, 18.0, INT),
    (13.5, 15.5, 13.5, 21.0, INT), (11.5, 15.5, 22.0, 15.5, INT),
    (16.5, 15.5, 16.5, 21.0, INT), (20.0, 15.5, 20.0, 21.0, INT),
    (20.0, 18.5, 24.5, 18.5, INT), (22.0, 13.5, 22.0, 18.5, INT),
    (19.5, 13.5, 24.5, 13.5, INT), (19.5, 8.3, 19.5, 13.5, INT),
    (19.5, 10.0, 24.5, 10.0, INT), (21.5, 8.3, 21.5, 10.0, INT),
    (11.5, 8.3, 11.5, 12.3, INT), (11.5, 12.3, 19.5, 12.3, INT),
    (11.5, 8.3, 17.4, 8.3, INT), (24.0, 0.0, 24.0, 5.2, INT),
]

# openings: (kind, orientation, wall_coord, start, end, swing, extra)
#  orientation 'h' = horizontal wall at y=wall_coord ; 'v' = vertical wall at x=wall_coord
doors = [
    ("double", "v", 8.3, 10.7, 12.5, +1),   # main entrance
    ("single", "h", 15.0, 6.0, 6.9, +1),     # majlis -> porch
    ("single", "h", 15.0, 9.6, 10.5, +1),    # majlis -> hall
    ("single", "h", 19.0, 9.8, 10.6, +1),    # guest bath
    ("single", "v", 13.5, 18.4, 19.2, -1),   # bath 2 (from kids 1)
    ("single", "h", 15.5, 12.1, 12.9, +1),   # store
    ("single", "h", 15.5, 15.4, 16.3, +1),   # kids 1
    ("single", "h", 15.5, 16.8, 17.7, +1),   # master
    ("open",   "v", 20.0, 16.2, 17.4, 0),    # master -> dressing
    ("single", "h", 18.5, 20.4, 21.2, +1),   # master bath
    ("single", "v", 22.0, 13.9, 14.8, +1),   # office
    ("single", "h", 13.5, 19.8, 20.7, -1),   # kids 2
    ("single", "h", 10.0, 22.0, 22.8, -1),   # bath 3
    ("open",   "h", 10.0, 19.8, 21.2, 0),    # wardrobe kids 2
    ("single", "v", 19.5, 3.6, 4.5, +1),     # dining -> kitchen
    ("open",   "v", 24.0, 3.8, 4.8, 0),      # kitchen -> laundry
    ("single", "h", 5.2, 25.6, 26.5, +1),    # laundry -> garden
    ("single", "h", 8.3, 18.0, 19.0, -1),    # courtyard -> garden (glazed)
]
windows = [
    ("h", 21.0, 6.6, 8.2), ("h", 21.0, 14.3, 15.7), ("h", 21.0, 17.5, 19.0),
    ("h", 21.0, 22.0, 23.5), ("v", 5.5, 16.2, 17.8), ("v", 24.5, 15.2, 16.8),
    ("v", 24.5, 11.0, 12.6), ("h", 3.2, 6.8, 9.5), ("h", 3.2, 10.8, 12.6),
    ("h", 3.2, 14.6, 16.8), ("v", 5.5, 4.6, 6.8), ("h", 5.2, 21.0, 22.6),
    ("v", 11.5, 9.4, 11.2), ("v", 19.5, 9.0, 9.8),
]
# courtyard opens to garden between (17.4, 8.3) and (19.5, 8.3) -> no wall there already


def wall_poly(x1, y1, x2, y2, t):
    return LineString([(x1, y1), (x2, y2)]).buffer(t / 2, cap_style="square", join_style="mitre")


def cut_rect(ori, c, a, b, depth=0.8):
    return box(a, c - depth / 2, b, c + depth / 2) if ori == "h" else box(c - depth / 2, a, c + depth / 2, b)


solid = unary_union([wall_poly(*w) for w in walls])
cuts = [cut_rect(o, c, a, b) for _, o, c, a, b, _ in doors] + [cut_rect(o, c, a, b) for o, c, a, b in windows]
solid = solid.difference(unary_union(cuts))


def add_poly_with_hatch(geom, layer, hatch_layer):
    polys = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
    for p in polys:
        msp.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={"layer": layer})
        for hole in p.interiors:
            msp.add_lwpolyline(list(hole.coords), close=True, dxfattribs={"layer": layer})
        h = msp.add_hatch(color=8, dxfattribs={"layer": hatch_layer})
        h.paths.add_polyline_path(list(p.exterior.coords)[:-1], is_closed=True, flags=1)
        for hole in p.interiors:
            h.paths.add_polyline_path(list(hole.coords)[:-1], is_closed=True, flags=0)


add_poly_with_hatch(solid, "A-WALL", "A-WALL-HATCH")

# ---------------------------------------------------------------- site wall with gates
site = LineString([(0, 0), (27.5, 0), (27.5, 23), (0, 23), (0, 0)]).buffer(SITE / 2, join_style="mitre")
site = site.difference(cut_rect("v", 0, 16.8, 18.6)).difference(cut_rect("v", 0, 4.6, 10.2))
for p in (site.geoms if hasattr(site, "geoms") else [site]):
    msp.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={"layer": "A-SITE-WALL"})
# pedestrian gate (two leaves) + sliding car gate
msp.add_line((0, 16.8), (-0.9, 17.7), dxfattribs={"layer": "A-DOOR"})
msp.add_line((0, 18.6), (-0.9, 17.7), dxfattribs={"layer": "A-DOOR"})
msp.add_arc((0, 16.8), 0.9 * math.sqrt(2), 90, 135, dxfattribs={"layer": "A-DOOR"})
msp.add_lwpolyline([(-0.35, 4.6), (-0.35, 10.2)], dxfattribs={"layer": "A-DOOR", "linetype": "DASHED"})
msp.add_lwpolyline([(-0.25, 4.6), (-0.25, 10.2)], dxfattribs={"layer": "A-DOOR"})


# ---------------------------------------------------------------- doors / windows symbols
def draw_door(kind, ori, c, a, b, s):
    L = {"layer": "A-DOOR"}
    w = b - a
    if kind == "open":
        return
    leaves = [(a, w, +1)] if kind == "single" else [(a, w / 2, +1), (b, w / 2, -1)]
    for hinge, lw, d in leaves:
        if ori == "h":
            hx, hy = hinge, c
            msp.add_line((hx, hy), (hx, hy + s * lw), dxfattribs=L)
            base = 0 if d > 0 else 180
            if s > 0:
                start, end = (base, 90) if d > 0 else (90, 180)
            else:
                start, end = (270, 360) if d > 0 else (180, 270)
        else:
            hx, hy = c, hinge
            msp.add_line((hx, hy), (hx + s * lw, hy), dxfattribs=L)
            if s > 0:
                start, end = (0, 90) if d > 0 else (270, 360)
            else:
                start, end = (90, 180) if d > 0 else (180, 270)
        msp.add_arc((hx, hy), lw, start, end, dxfattribs=L)


for d in doors:
    draw_door(*d)

for ori, c, a, b in windows:
    t = EXT if ori == "h" and c in (21.0, 3.2, 5.2) or ori == "v" and c in (5.5, 24.5) else INT
    for off in (-t / 2, -0.03, 0.03, t / 2):
        if ori == "h":
            msp.add_line((a, c + off), (b, c + off), dxfattribs={"layer": "A-WINDOW"})
        else:
            msp.add_line((c + off, a), (c + off, b), dxfattribs={"layer": "A-WINDOW"})
    for e in (a, b):
        p1, p2 = ((e, c - t / 2), (e, c + t / 2)) if ori == "h" else ((c - t / 2, e), (c + t / 2, e))
        msp.add_line(p1, p2, dxfattribs={"layer": "A-WINDOW"})

# ---------------------------------------------------------------- stairs
for i in range(17):
    x = 12.3 + i * 0.4
    msp.add_line((x, 12.4), (x, 13.45), dxfattribs={"layer": "A-STAIR"})
msp.add_lwpolyline([(12.3, 12.9), (18.6, 12.9)], dxfattribs={"layer": "A-STAIR"})
msp.add_lwpolyline([(18.3, 13.05), (18.6, 12.9), (18.3, 12.75)], dxfattribs={"layer": "A-STAIR"})
msp.add_text("UP", height=0.22, dxfattribs={"layer": "A-TEXT", "style": "ARCH"}).set_placement(
    (12.4, 12.95), align=TextEntityAlignment.BOTTOM_LEFT)


# ---------------------------------------------------------------- furniture helpers
F = {"layer": "A-FURN"}


def rect(x, y, w, h, layer="A-FURN"):
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True, dxfattribs={"layer": layer})


def bed(x, y, w, h, pillow_top=True):
    rect(x, y, w, h)
    py = y + h - 0.55 if pillow_top else y + 0.05
    if w > 1.2:
        rect(x + 0.1, py, w / 2 - 0.15, 0.45); rect(x + w / 2 + 0.05, py, w / 2 - 0.15, 0.45)
    else:
        rect(x + 0.1, py, w - 0.2, 0.45)
    fy = y + h * 0.55 if pillow_top else y + h * 0.45
    msp.add_line((x, fy), (x + w, fy), dxfattribs=F)


def wc(x, y, rot=0):
    blk = "WC"
    if blk not in doc.blocks:
        b = doc.blocks.new(blk)
        b.add_lwpolyline([(-0.25, 0), (0.25, 0), (0.25, 0.2), (-0.25, 0.2)], close=True)
        b.add_ellipse((0, 0.48), major_axis=(0, 0.3), ratio=0.65)
    msp.add_blockref(blk, (x, y), dxfattribs={"layer": "A-FURN", "rotation": rot})


def basin(x, y, rot=0):
    if "BASIN" not in doc.blocks:
        b = doc.blocks.new("BASIN")
        b.add_lwpolyline([(-0.3, 0), (0.3, 0), (0.3, 0.45), (-0.3, 0.45)], close=True)
        b.add_ellipse((0, 0.22), major_axis=(0.2, 0), ratio=0.7)
    msp.add_blockref("BASIN", (x, y), dxfattribs={"layer": "A-FURN", "rotation": rot})


def shower(x, y, w, h):
    rect(x, y, w, h)
    msp.add_line((x, y), (x + w, y + h), dxfattribs=F)
    msp.add_line((x, y + h), (x + w, y), dxfattribs=F)


def tree(x, y, r):
    msp.add_circle((x, y), r, dxfattribs={"layer": "A-PLANT"})
    for k in range(10):
        a = math.radians(k * 36)
        msp.add_line((x, y), (x + r * math.cos(a), y + r * math.sin(a)), dxfattribs={"layer": "A-PLANT"})
    msp.add_circle((x, y), r * 0.15, dxfattribs={"layer": "A-PLANT"})


def chairs_around(cx, cy, w, h):
    rect(cx - w / 2, cy - h / 2, w, h)
    n = max(2, int(w / 0.6))
    for i in range(n):
        x = cx - w / 2 + (i + 0.5) * w / n - 0.2
        rect(x, cy + h / 2 + 0.05, 0.4, 0.4)
        rect(x, cy - h / 2 - 0.45, 0.4, 0.4)


# Majlis: L/U floor seating + table + TV unit
rect(5.75, 15.3, 0.7, 3.45); rect(5.75, 18.05, 5.2, 0.7); rect(10.25, 15.3, 0.7, 2.75)
rect(7.6, 16.3, 1.8, 1.2)
# guest bath
wc(6.3, 20.85, 180); basin(7.6, 20.85, 180); basin(8.4, 20.85, 180); shower(10.2, 19.6, 1.2, 1.25)
# bath 2
wc(12.0, 20.85, 180); basin(13.35, 19.6, 90); shower(11.7, 18.2, 1.0, 1.0)
# store shelving
rect(11.7, 15.7, 0.5, 2.1); rect(12.9, 15.7, 0.5, 2.1)
# kids 1
bed(14.0, 18.4, 1.2, 2.1); rect(15.4, 20.35, 0.5, 0.45); rect(13.7, 15.7, 1.4, 0.6)
# master
bed(17.2, 18.75, 1.9, 2.1); rect(16.65, 20.35, 0.45, 0.45); rect(19.2, 20.35, 0.45, 0.45)
# dressing
rect(20.2, 15.7, 0.6, 2.6); rect(21.3, 15.7, 0.6, 2.6)
# master bath
basin(21.6, 20.85, 180); basin(22.4, 20.85, 180); wc(23.4, 20.85, 180); rect(23.6, 18.7, 0.75, 1.7)
msp.add_ellipse((23.97, 19.55), major_axis=(0, 0.7), ratio=0.4, dxfattribs=F)
# office
rect(23.6, 15.6, 0.7, 1.6); rect(23.0, 16.15, 0.45, 0.45); rect(22.2, 17.6, 2.1, 0.6)
# kids 2
bed(22.1, 11.1, 2.1, 1.2); rect(23.75, 12.4, 0.5, 0.45)
msp.add_line((22.1, 11.1), (22.1, 12.3), dxfattribs=F)
# bath 3
wc(24.35, 9.15, 90); basin(23.0, 8.45, 0); shower(21.7, 8.5, 0.95, 1.3)
# wardrobe kids 2
rect(19.7, 8.5, 1.6, 0.6)

# living: sofas, coffee table, armchairs
rect(5.8, 3.6, 0.85, 3.9); rect(5.8, 6.7, 3.6, 0.85); rect(10.5, 3.6, 0.85, 3.3)
rect(8.5, 3.6, 1.9, 0.8)
msp.add_ellipse((8.3, 5.3), major_axis=(1.5, 0), ratio=0.55, dxfattribs=F)
rect(7.0, 3.6, 0.8, 0.8)
msp.add_circle((9.9, 5.0), 0.25, dxfattribs=F)
# dining 4x3 zone: table for 6
chairs_around(15.4, 5.6, 1.8, 0.9)
# kitchen: counters + island
rect(19.75, 0.15, 0.6, 4.9); rect(19.75, 0.15, 4.0, 0.6); rect(21.4, 2.0, 1.6, 0.9)
for i in range(4):
    msp.add_circle((19.95 + (i % 2) * 0.25, 1.4 + (i // 2) * 0.25), 0.09, dxfattribs=F)
basin(22.5, 0.2, 0)
# laundry: washer / dryer
rect(24.2, 0.15, 0.6, 0.6); rect(24.9, 0.15, 0.6, 0.6)
rect(26.8, 0.4, 0.6, 3.6)
for x, t in ((24.5, "WM"), (25.2, "DR")):
    msp.add_text(t, height=0.15, dxfattribs={"layer": "A-TEXT", "style": "ARCH"}).set_placement(
        (x, 0.45), align=TextEntityAlignment.MIDDLE_CENTER)

# courtyard: round fountain + planting
msp.add_circle((14.5, 10.3), 1.1, dxfattribs={"layer": "A-PLANT"})
msp.add_circle((14.5, 10.3), 0.75, dxfattribs={"layer": "A-PLANT"})
msp.add_circle((14.5, 10.3), 0.2, dxfattribs={"layer": "A-PLANT"})
for x, y, r in ((16.6, 11.3, 0.7), (18.2, 11.2, 0.7), (12.3, 9.2, 0.5), (18.6, 9.4, 0.5)):
    tree(x, y, r)

# car in parking
rect(2.6, 2.3, 1.9, 4.6)
rect(2.8, 4.3, 1.5, 1.2)
msp.add_line((2.8, 3.2), (4.3, 3.2), dxfattribs=F)
msp.add_line((2.8, 6.0), (4.3, 6.0), dxfattribs=F)

# landscaping
for x, y, r in ((1.2, 21.6, 0.9), (2.8, 21.9, 0.7), (13.3, 1.6, 0.8), (15.0, 1.7, 0.9),
                (17.0, 1.5, 1.1), (18.4, 2.2, 0.6), (21.3, 7.1, 0.7), (22.9, 7.0, 0.8)):
    tree(x, y, r)
# garden stepping stones along the courtyard -> garden path
for i in range(14):
    cx, cy = 18.0 + i * 0.65, 6.0 + 0.9 * math.sin(i * 0.8)
    if cx < 27:
        msp.add_ellipse((cx, cy), major_axis=(0.22, 0.05), ratio=0.65, dxfattribs={"layer": "A-PLANT"})
# deck lines right of kids 2
for i in range(7):
    y = 8.6 + i * 0.6
    msp.add_line((24.75, y), (27.3, y), dxfattribs={"layer": "A-PLANT"})


# ---------------------------------------------------------------- labels
def label(x, y, name, size=None, h=0.32):
    msp.add_text(name, height=h, dxfattribs={"layer": "A-TEXT", "style": "ARCH"}).set_placement(
        (x, y), align=TextEntityAlignment.MIDDLE_CENTER)
    if size:
        msp.add_text(size, height=h * 0.75, dxfattribs={"layer": "A-TEXT", "style": "ARCH"}).set_placement(
            (x, y - h * 1.3), align=TextEntityAlignment.MIDDLE_CENTER)


label(8.5, 17.0, "MAJLIS", "6.00 x 4.00 m")
label(8.6, 20.0, "BATH", h=0.25)
label(12.5, 19.2, "BATH", h=0.22)
label(12.5, 16.8, "STORE", h=0.2)
label(15.0, 17.2, "KIDS 1", "3.00 x 5.00 m")
label(18.25, 17.2, "MASTER", "3.50 x 5.00 m")
label(22.2, 19.6, "BATH", h=0.25)
label(21.0, 18.0, "DRESS", h=0.2)
label(23.25, 14.6, "OFFICE", h=0.25)
label(21.0, 12.0, "KIDS 2", "3.00 x 5.00 m", h=0.28)
label(22.9, 9.6, "BATH", h=0.2)
label(16.8, 14.5, "CORRIDOR", h=0.25)
label(9.9, 12.0, "HALL", h=0.28)
label(15.8, 9.0, "COURTYARD", h=0.28)
label(8.3, 5.3, "LIVING ROOM", "8.00 x 5.00 m")
label(15.4, 7.3, "DINING", "4.00 x 3.00 m", h=0.28)
label(22.0, 3.4, "KITCHEN", "4.50 x 5.00 m", h=0.28)
label(25.7, 2.9, "LAUNDRY", h=0.25)
label(6.9, 12.5, "PORCH", h=0.25)
label(6.9, 11.7, "+0.00", h=0.2)
label(3.5, 8.0, "PARKING", h=0.28)
label(22.5, 6.4, "GARDEN", h=0.28)
msp.add_text("ENTRANCE", height=0.3, dxfattribs={"layer": "A-TEXT", "style": "ARCH"}).set_placement(
    (-4.2, 17.7), align=TextEntityAlignment.MIDDLE_LEFT)
msp.add_lwpolyline([(-1.9, 17.7), (-1.1, 17.7)], dxfattribs={"layer": "A-TEXT"})
msp.add_lwpolyline([(-1.35, 17.85), (-1.1, 17.7), (-1.35, 17.55)], dxfattribs={"layer": "A-TEXT"})

# title
msp.add_text("FLOOR PLAN", height=1.0, dxfattribs={"layer": "A-TEXT", "style": "ARCH"}).set_placement(
    (13.75, -2.2), align=TextEntityAlignment.MIDDLE_CENTER)
msp.add_text("SCALE 1:100", height=0.4, dxfattribs={"layer": "A-TEXT", "style": "ARCH"}).set_placement(
    (13.75, -3.4), align=TextEntityAlignment.MIDDLE_CENTER)
msp.add_line((10.5, -2.9), (17.0, -2.9), dxfattribs={"layer": "A-TEXT"})


# ---------------------------------------------------------------- section marks
def section(p1, p2, name, arrow_dir):
    msp.add_line(p1, p2, dxfattribs={"layer": "A-SECTION", "linetype": "DASHDOT"})
    for p in (p1, p2):
        tip = (p[0] + arrow_dir[0] * 0.9, p[1] + arrow_dir[1] * 0.9)
        msp.add_line(p, tip, dxfattribs={"layer": "A-SECTION"})
        msp.add_text(name, height=0.45, dxfattribs={"layer": "A-SECTION", "style": "ARCH"}).set_placement(
            (tip[0] + arrow_dir[0] * 0.4, tip[1] + arrow_dir[1] * 0.4), align=TextEntityAlignment.MIDDLE_CENTER)


section((-1.5, 12.95), (29.0, 12.95), "A", (0, 1))
section((20.3, -1.2), (20.3, 24.5), "B", (1, 0))

# ---------------------------------------------------------------- overall dimensions
DIMOV = {"dimlfac": 1, "dimdec": 2, "dimtxt": 0.3, "dimasz": 0.25, "dimexo": 0.1, "dimexe": 0.2, "dimgap": 0.08}
msp.add_linear_dim(base=(0, 24.8), p1=(0, 23), p2=(27.5, 23), dxfattribs={"layer": "A-TEXT"}, override=DIMOV).render()
msp.add_linear_dim(base=(29.6, 0), p1=(27.5, 0), p2=(27.5, 23), angle=90, dxfattribs={"layer": "A-TEXT"}, override=DIMOV).render()
msp.add_linear_dim(base=(0, 22.2), p1=(5.5, 21), p2=(24.5, 21), dxfattribs={"layer": "A-TEXT"}, override=DIMOV).render()
msp.add_linear_dim(base=(4.4, 0), p1=(5.5, 3.2), p2=(5.5, 21), angle=90, dxfattribs={"layer": "A-TEXT"}, override=DIMOV).render()

doc.saveas(OUT)
print("saved", OUT)

# ---------------------------------------------------------------- preview PNG
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy

    fig = plt.figure(figsize=(14, 12.5))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp)
    fig.savefig(OUT.with_name("floor_plan_preview.png"), dpi=110)
    print("preview saved")
except Exception as e:  # preview is optional
    print("preview skipped:", e)
