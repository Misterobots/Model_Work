#!/usr/bin/env python3
"""Parametric generator for the HydroLink Archimedes-screw lift.

Builds every new printed part as a watertight solid (manifold3d CSG), writes
binary STLs in print orientation to cad/lift/stl/, a world-frame assembly
preview to cad/lift/stl/_assembly.stl, and a fit/clearance report to
cad/lift/stl/REPORT.md.

    pip install -r cad/requirements.txt
    python3 cad/lift/build.py            # all parts
    python3 cad/lift/build.py --risers 95 120   # extra riser heights

All dimensions are mm. Interface numbers that come from the HydroLink /
FlowLab 3MF files are marked MEASURED; see docs/INTERFACES.md and
cad/tools/measure_hydrolink.py for how they were taken.
"""
import argparse
import math
import struct
from pathlib import Path

import numpy as np
import manifold3d as mf

M, CS = mf.Manifold, mf.CrossSection
mf.set_circular_segments(96)

# ---------------------------------------------------------------- parameters
# Lift geometry
INCLINE_DEG = 22.0       # trough incline; must stay below FLIGHT_ANGLE (checked)
SCREW_R = 45.0           # screw outer radius (D = 90)
CORE_R = 12.0            # screw core radius
PITCH = 135.0            # one turn per segment (1.5 x D)
N_SEG = 4                # segments; lift grows ~50 mm per extra segment
FLIGHT_W = 6.0           # tangential flight width -> ~2.6 mm normal thickness at tip
ROD_D = 6.0              # stainless rod
ROD_CLEAR = 0.4          # bore = ROD_D + ROD_CLEAR
HEX_AF = 16.0            # segment-to-segment hex spigot (across flats)
HEX_LEN = 8.0
FIT = 0.35               # printed sliding fit allowance (per side, on sockets)

# Trough
TROUGH_CLEAR = 2.0       # radial screw-to-trough clearance
WALL = 4.0               # trough wall (>= 4 perimeters at 0.42 mm)
RIM_ABOVE_AXIS = 8.0     # trough side walls rise this far above the screw axis
FLANGE_W = 9.0           # flange land beyond the trough outer surface
FLANGE_T = 6.0
BOLT_D = 3.4             # M3 clearance
TROUGH_MAX_PIECE = 215.0 # trough is split into equal pieces no longer than this
TAIL_S = -12.0           # trough tail (below screw tail at s=0)

# Drive
BEARING_OD, BEARING_W = 13.0, 5.0     # 686ZZ (6x13x5)
MOTOR_OD = 25.0                       # JGA25-370 gearbox diameter
MOTOR_STANDOFF = 30.0                 # bearing boss face -> gearbox face
CLAMP_LEN = 32.0
COUPLER_LEN = 25.0                    # 4 mm -> 6 mm flexible coupler

# Head box (receives the screw discharge, spout feeds the slide)
HB_WALL = 5.0
HB_FLOOR = 10.0
HB_INNER_W = 112.0       # inside width (y)
HB_DROP = 20.0           # floor this far below the trough's lowest inner point
HB_SPOUT_W = 90.0        # spout inner width (fits inside a 120 mm HydroLink track)
HB_SPOUT_WALL_H = 28.0
SLIDE_OFFSET_Y = 135.0   # slide centreline offset from the lift axis (side by side)
SPOUT_OVERHANG = 30.0    # launder runs this far forward of the head-box floor
SPOUT_INSERT = 20.0      # how far the spout reaches into the first track's open end
SPOUT_DROP = 10.0        # spout floor -> track inner floor at the entry
TIP_LIFT = 6.0           # pour tip rides this far above the track floor (clears the ~6.5 mm seal ridge
                         # in the track's 10 mm end zone, MEASURED by check_fit.py)

# Site / HydroLink interfaces (MEASURED from the 3MF files)
BASIN_FLOOR_TOP = 13.0   # Big basin inner floor above table   (MEASURED 13)
BASIN_RIM = 70.0         # basin & track height                (MEASURED 70)
BASIN_HALF_OUT = 125.0   # Big basin is a 250 mm rounded square (MEASURED)
BASIN_HALF_IN = 123.0    # inner half-width                    (MEASURED, ~2 mm walls)
BASIN_CORNER_R = 69.0    # corner radius, from slice area      (MEASURED, approx.)
TRACK_FLOOR = 9.5        # track inner floor above its underside (MEASURED 9.5)
TRACK_INNER_W = 120.0    # track inner width at the rim        (MEASURED ~120)
# Track channel (inner surface) half-profile: (across, height above inner floor).
# MEASURED from a mid-length section of the HydroLink "I" (cad/tools/measure_hydrolink.py).
TRACK_PROFILE = [(0.0, 0.0), (15.3, 1.9), (23.7, 4.8), (31.5, 8.8), (42.0, 16.9),
                 (50.5, 27.1), (56.5, 38.8), (59.9, 51.7), (60.5, 60.5)]
FLOATY = (20.0, 20.0, 18.5)  # FlowLab Floaty bounding box      (MEASURED)
BED = 256.0              # Bambu P1S build volume (project profile in both files)

BASIN_TAIL_GAP = 80.0    # trough tail to the basin wall behind it (keeps the tail out of the rounded corner)
BASIN_CENTER_Y = 63.0    # basin centre offset from the lift axis toward the slide

# Slide chain, top to bottom (all rigid HydroLink joints, so the chain is tilted
# as one piece and only descends along the lift direction). Lengths MEASURED.
SLIDE_CHAIN = [("I", 200.0), ("Flow modifier body + filter (staging gate)", 18.0), ("I", 200.0)]
SLIDE_CLEAR_RIM = 3.0    # last track underside above the basin rim

# Slide risers
RISER_PAD = (100.0, 30.0)   # top pad: across the track x along the track

OUT = Path(__file__).resolve().parent / "stl"

# ------------------------------------------------------------------ helpers
TH = math.radians(INCLINE_DEG)
C, S = math.cos(TH), math.sin(TH)
R_IN = SCREW_R + TROUGH_CLEAR
R_OUT = R_IN + WALL
ROD_BORE = ROD_D + ROD_CLEAR


def axis_to_world():
    """3x4 matrix: lift-local frame (Z = screw axis, Y = trough opening side,
    X = across) -> world (X horizontal up-slope, Y across, Z up)."""
    ex, ey, ez = (0, 1, 0), (-S, 0, C), (C, 0, S)
    return [[ex[0], ey[0], ez[0], 0], [ex[1], ey[1], ez[1], 0], [ex[2], ey[2], ez[2], 0]]


def place(m, origin):
    return m.transform(axis_to_world()).translate(origin)


def hexagon(af, extra=0.0):
    r = (af / 2 + extra) / math.cos(math.pi / 6)
    return CS([[(r * math.cos(math.pi / 6 + k * math.pi / 3), r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]])


def key_nub(extra=0.0):
    # orientation key so segments only stack with the flight in phase
    w = 3.0 + 2 * extra
    return CS.square((4.0 + extra, w)).translate((HEX_AF / 2 - 0.5, -w / 2))


def u_section(r, rim, w_extra=0.0):
    """Trough U: half-disc below the axis + rectangle up to `rim` above it."""
    half = CS.circle(r) ^ CS.square((2 * r + 2, r + 1)).translate((-r - 1, -r - 1))
    return half + CS.square((2 * r + 2 * w_extra, rim + 0.0)).translate((-r - w_extra, -0.01))


def channel_section():
    """HydroLink track channel (inner void) as a 2D section, floor at y=0."""
    right = TRACK_PROFILE
    pts = [(x, y) for x, y in right] + [(-x, y) for x, y in reversed(right)][1:-1]
    return CS([pts])


def flange_bolts():
    rf = R_OUT + FLANGE_W / 2
    pts = [(-rf, RIM_ABOVE_AXIS - 4), (rf, RIM_ABOVE_AXIS - 4)]
    for a in (-35, -145):
        pts.append((rf * math.cos(math.radians(a)), rf * math.sin(math.radians(a))))
    return pts


def bolt_holes(pts, length, z0):
    out = M()
    for x, y in pts:
        out += M.cylinder(length, BOLT_D / 2).translate((x, y, z0))
    return out


def flange(z0):
    sec = u_section(R_OUT + FLANGE_W, RIM_ABOVE_AXIS) - u_section(R_IN, RIM_ABOVE_AXIS + 5)
    body = sec.extrude(FLANGE_T).translate((0, 0, z0))
    return body - bolt_holes(flange_bolts(), FLANGE_T + 2, z0 - 1)


def to_bed(m):
    """Drop a part onto the bed at the origin."""
    b = m.bounding_box()
    return m.translate((-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]))


def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float64)
    f = np.asarray(mesh.tri_verts)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)
    with open(path, "wb") as fh:
        fh.write(b"HydroLink screw lift".ljust(80, b" "))
        fh.write(struct.pack("<I", len(f)))
        rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec["n"], rec["v"] = n, tri
        fh.write(rec.tobytes())


# -------------------------------------------------------------------- parts
def screw_segment():
    flight_cs = CS.square((SCREW_R - CORE_R + 1.0, FLIGHT_W)).translate((CORE_R - 1.0, -FLIGHT_W / 2))
    flight = flight_cs.extrude(PITCH, n_divisions=180, twist_degrees=-360.0)
    core = M.cylinder(PITCH, CORE_R)
    spigot = (hexagon(HEX_AF) + key_nub()).extrude(HEX_LEN - 0.4).translate((0, 0, PITCH))
    socket = (hexagon(HEX_AF, FIT) + key_nub(FIT)).extrude(HEX_LEN).translate((0, 0, -0.01))
    bore = M.cylinder(PITCH + HEX_LEN + 2, ROD_BORE / 2).translate((0, 0, -1))
    return (core + flight + spigot) - socket - bore


def drive_hub():
    h = HEX_LEN + 10
    body = M.cylinder(h, CORE_R)
    socket = (hexagon(HEX_AF, FIT) + key_nub(FIT)).extrude(HEX_LEN).translate((0, 0, -0.01))
    bore = M.cylinder(h + 2, ROD_BORE / 2).translate((0, 0, -1))
    grub = M.cylinder(CORE_R + 2, 1.25).rotate((0, 90, 0)).translate((0, 0, HEX_LEN + 5))  # tap M3
    return body - socket - bore - grub


def trough(s0, s1, tail=False):
    length = s1 - s0
    sec = u_section(R_OUT, RIM_ABOVE_AXIS) - u_section(R_IN, RIM_ABOVE_AXIS + 5)
    body = sec.extrude(length)
    if tail:
        # open tail (water & minis enter axially), cross-bar at axis height + bushing boss
        bar = CS.square((2 * R_IN + 2, 8)).translate((-R_IN - 1, -4)).extrude(6)
        boss = M.cylinder(10, 9)
        hole = M.cylinder(10, ROD_BORE / 2).translate((0, 0, 1.5))
        body += (bar + boss) - hole
    else:
        body += flange(0)
    body += flange(length - FLANGE_T)
    # 45° chamfer under the far flange so the trough prints standing up without supports
    z1 = length - FLANGE_T
    lip = u_section(R_OUT + FLANGE_W, RIM_ABOVE_AXIS).extrude(0.01).translate((0, 0, z1))
    root = u_section(R_OUT, RIM_ABOVE_AXIS).extrude(0.01).translate((0, 0, z1 - FLANGE_W))
    chamfer = M.batch_hull([lip, root]) - u_section(R_OUT - 0.5, RIM_ABOVE_AXIS + 50).extrude(FLANGE_W + 2).translate((0, 0, z1 - FLANGE_W - 1))
    chamfer -= bolt_holes(flange_bolts(), FLANGE_W + 2, z1 - FLANGE_W - 1)
    body += chamfer
    return body, s0


# --- world layout -----------------------------------------------------------
def layout():
    """Axial stations (s) and world heights; table at z=0, tail of the trough
    resting on the Big basin floor."""
    L = {}
    L["screw_top_s"] = N_SEG * PITCH
    L["trough_top_s"] = L["screw_top_s"] + 4.0
    L["front_s"] = L["trough_top_s"] + HB_WALL     # head-box front wall inner plane
    # lowest point of the trough tail = outer circle bottom (flange there is lugs only)
    L["axis_tail_z"] = BASIN_FLOOR_TOP + R_OUT * C
    L["origin_tail"] = np.array([0.0, 0.0, L["axis_tail_z"]]) - np.array([C, 0, S]) * TAIL_S
    L["O"] = L["origin_tail"] + np.array([C, 0, S]) * L["front_s"]
    # head box frame (relative to O, world axes)
    L["hb_floor_z"] = -R_IN * C - HB_DROP
    L["hb_front_floor_x"] = -L["hb_floor_z"] * S / C
    L["hb_back_x"] = L["hb_front_floor_x"] + HB_SPOUT_W + 2 * HB_WALL + 12
    L["rod_back_z"] = L["hb_back_x"] * S / C
    L["hb_top_z"] = L["rod_back_z"] + 22
    L["hb_base_world_z"] = L["O"][2] + L["hb_floor_z"] - HB_FLOOR
    L["spout_floor_world_z"] = L["O"][2] + L["hb_floor_z"]
    return L


def head_box(L):
    zf, xb, zt = L["hb_floor_z"], L["hb_back_x"], L["hb_top_z"]
    W = HB_INNER_W
    d = np.array([C, 0, S])
    big = 600.0
    # half-space d.p >= k  as a big box
    def halfspace(k):
        hs = M.cube((big, big, big), center=True).translate((big / 2, 0, 0))
        return hs.rotate((0, -INCLINE_DEG, 0)).translate(tuple(d * k))
    outer = M.cube((xb + HB_WALL + 250, W + 2 * HB_WALL, zt - (zf - HB_FLOOR))).translate((-250, -W / 2 - HB_WALL, zf - HB_FLOOR))
    outer = outer ^ halfspace(-HB_WALL)
    inner = M.cube((xb + 250, W, zt - zf + 5)).translate((-250, -W / 2, zf)) ^ halfspace(0.0)
    box = outer - inner
    # inlet: trough U profile through the inclined front wall
    inlet = u_section(R_IN, RIM_ABOVE_AXIS + 60).extrude(40).translate((0, 0, -20))
    box -= place(inlet, (0, 0, 0))
    box -= place(bolt_holes(flange_bolts(), 40, -20), (0, 0, 0))
    # rod boss + 686 bearing pocket on the back wall
    t_back = (xb + HB_WALL) / C            # axial distance O -> back wall outer face
    boss = M.cylinder(14 + 8, 11).translate((0, 0, xb / C - 6))
    box += place(boss, (0, 0, 0)) - inner
    box += place(M.cylinder(8 + 6, 11).translate((0, 0, t_back - 6)), (0, 0, 0))
    L["boss_face_s_rel"] = t_back + 8
    box -= place(M.cylinder(200, (ROD_BORE + 0.4) / 2).translate((0, 0, 0)), (0, 0, 0))
    box -= place(M.cylinder(BEARING_W + 0.2, BEARING_OD / 2 + 0.1).translate((0, 0, t_back + 8 - BEARING_W - 0.2 + 0.01)), (0, 0, 0))
    # motor-mount bolt holes in the back wall (horizontal, x direction)
    zc = L["rod_back_z"]
    for dy in (-20, 20):
        for dz in (-20, 20):
            box -= M.cylinder(HB_WALL + 20, BOLT_D / 2).rotate((0, 90, 0)).translate((xb - 10, dy, zc + dz))
    L["motor_bolts"] = [(dy, dz) for dy in (-20, 20) for dz in (-20, 20)]
    # Side launder: an opening in the +y wall at floor level feeds a channel that
    # runs alongside the box back toward the basin (-x) and pours end-on into the
    # open top end of the first slide track, whose centreline is SLIDE_OFFSET_Y.
    x0 = L["hb_front_floor_x"] + 6
    x1 = xb - 4
    x_lo = L["hb_front_floor_x"] - SPOUT_OVERHANG
    y_hi = SLIDE_OFFSET_Y + HB_SPOUT_W / 2
    box -= M.cube((x1 - x0, HB_WALL + 2, HB_SPOUT_WALL_H + 200)).translate((x0, W / 2 - 1, zf))
    l_out = M.cube((x1 - x_lo + 4, y_hi + 4 - W / 2, HB_SPOUT_WALL_H + HB_FLOOR)).translate((x_lo, W / 2, zf - HB_FLOOR))
    l_in = M.cube((x1 - x_lo + 1, y_hi - W / 2 + 1, HB_SPOUT_WALL_H + 10)).translate((x_lo - 1, W / 2 - 1, zf))
    box += l_out - l_in
    # Pour tip: follows the track's rounded channel (2 mm gap, 3 mm wall) so it can
    # reach SPOUT_INSERT into the first track's open end without touching it.
    xt = x_lo + SPOUT_INSERT
    box -= M.cube((SPOUT_INSERT + 2, y_hi - W / 2 + 10, HB_SPOUT_WALL_H + 20)).translate((x_lo - 1, W / 2 + HB_WALL, zf - 10))
    box += M.cube((3, y_hi + 4 - W / 2 - HB_WALL, HB_SPOUT_WALL_H + HB_FLOOR)).translate((xt, W / 2 + HB_WALL, zf - HB_FLOOR))
    ch = channel_section()
    z_floor = zf - SPOUT_DROP + TIP_LIFT                # tip profile floor (track floor + lift)
    clip = CS.square((300, HB_SPOUT_WALL_H + 5)).translate((-150, SPOUT_DROP - TIP_LIFT - 4))
    tip_out = (ch.offset(-1.0, mf.JoinType.Round) ^ clip)
    tip_in = ch.offset(-3.5, mf.JoinType.Round) ^ CS.square((300, 200)).translate((-150, SPOUT_DROP - TIP_LIFT))
    def to_world(cs, length, x0):
        # section plane: (across, up) -> world (y, z); extrude along -x from x0
        return cs.extrude(length).rotate((90, 0, 90)).translate((x0, SLIDE_OFFSET_Y, z_floor))
    tip = to_world(tip_out, SPOUT_INSERT + 3, x_lo) - to_world(tip_in, SPOUT_INSERT + 10, x_lo - 2)
    box += tip
    box -= to_world(tip_in, 8, xt - 2)                  # open the end plate into the tip
    L["spout_end_x"] = x_lo
    return box


def motor_mount(L):
    """Plate bolted to the head-box back wall + clamp tube coaxial with the rod."""
    xb, zc = L["hb_back_x"] + HB_WALL, L["rod_back_z"]
    plate = M.cube((5, 64, 64)).translate((xb, -32, zc - 32))
    plate -= M.cylinder(20, 12.5).rotate((0, 90, 0)).translate((xb - 5, 0, L["rod_back_z"] + (HB_WALL) * S / C))
    for dy, dz in L["motor_bolts"]:
        plate -= M.cylinder(20, BOLT_D / 2).rotate((0, 90, 0)).translate((xb - 5, dy, zc + dz))
    # clamp tube along the axis
    s_face = L["boss_face_s_rel"] + MOTOR_STANDOFF
    tube = M.cylinder(CLAMP_LEN, MOTOR_OD / 2 + 3.5).translate((0, 0, s_face))
    bore = M.cylinder(CLAMP_LEN + 2, MOTOR_OD / 2 + 0.25).translate((0, 0, s_face - 1))
    slit = M.cube((2.0, 30, CLAMP_LEN + 2)).translate((-1, 0, s_face - 1))
    ears = M.cube((14, 10, 12)).translate((-7, MOTOR_OD / 2 + 1, s_face + CLAMP_LEN / 2 - 6))
    ear_hole = M.cylinder(20, BOLT_D / 2).rotate((0, 90, 0)).translate((-10, MOTOR_OD / 2 + 7, s_face + CLAMP_LEN / 2))
    ring = M.cylinder(3, MOTOR_OD / 2 + 3.5).translate((0, 0, s_face))
    clamp = place(tube + ears - bore - slit - ear_hole, (0, 0, 0))
    # struts: hull between plate face and the tube's first ring, hollowed for the coupler
    strut = M.batch_hull([plate ^ M.cube((1, 64, 64)).translate((xb + 4, -32, zc - 32)), place(ring, (0, 0, 0))])
    clear = place(M.cylinder(s_face - L["boss_face_s_rel"] + 30, 12.5).translate((0, 0, L["boss_face_s_rel"] - 20)), (0, 0, 0))
    win_a = place(M.cube((60, 16, MOTOR_STANDOFF - 8)).translate((-30, -8, L["boss_face_s_rel"] + 4)), (0, 0, 0))
    mount = plate + (strut - clear - win_a) + clamp
    mount -= M.cube((200, 200, 200)).translate((xb - 200, -100, zc - 100))  # nothing behind the wall face
    L["motor_face_s_rel"] = s_face
    return mount


def motor_hood():
    r_in = MOTOR_OD / 2 + 3.5 + 0.5
    cup = M.cylinder(80, r_in + 2) - M.cylinder(80, r_in).translate((0, 0, 2))
    slot = M.cube((8, 2 * r_in + 10, 12)).translate((-4, -r_in - 5, 70))
    return cup - slot


def head_box_stand(L, footprint):
    h = L["hb_base_world_z"]
    x0, y0, x1, y1 = footprint
    outer = M.cube((x1 - x0, y1 - y0, h)).translate((x0, y0, 0))
    inner = M.cube((x1 - x0 - 10, y1 - y0 - 10, h + 2)).translate((x0 + 5, y0 + 5, -1))
    frame = outer - inner
    # windows to save plastic, leaving corner posts
    for ax in (0, 1):
        span = (x1 - x0) if ax == 0 else (y1 - y0)
        win = M.cube((span - 30, 400, h - 30) if ax == 0 else (400, span - 30, h - 30))
        win = win.translate((x0 + 15, -200, 15) if ax == 0 else (-200, y0 + 15, 15))
        frame -= win
    lip = M.cube((x1 - x0 + 6, y1 - y0 + 6, 4)).translate((x0 - 3, y0 - 3, h)) - M.cube((x1 - x0 + 0.6, y1 - y0 + 0.6, 6)).translate((x0 - 0.3, y0 - 0.3, h - 1))
    return frame + lip


def riser(h, slope=0.0):
    """Riser column; the top pad is tilted to the slide slope (local +y = downhill)."""
    px, py = RISER_PAD
    top = h + py / 2 * slope + 1
    col = M.cube((px * 0.6, py, top)).translate((-px * 0.3, -py / 2, 0))
    base = M.cube((px, py + 40, 4)).translate((-px / 2, -(py + 40) / 2, 0))
    pad = M.cube((px, py, 8)).translate((-px / 2, -py / 2, top - 8))
    hole = M.cube((px * 0.6 - 8, py - 8, top - 16)).translate((-px * 0.3 + 4, -py / 2 + 4, 4))
    r = col + base + pad - hole
    n = np.array([0.0, -slope, -1.0]); k = np.linalg.norm(n)
    return r.trim_by_plane(tuple(n / k), -h / k)


def basin_limit(xr):
    """Half-width of the Big basin interior at x offset xr from its centre
    (rounded square: straight walls plus BASIN_CORNER_R corners)."""
    straight = BASIN_HALF_IN - BASIN_CORNER_R
    ax = abs(xr)
    if ax <= straight:
        return BASIN_HALF_IN
    if ax >= BASIN_HALF_IN:
        return 0.0
    return straight + math.sqrt(BASIN_CORNER_R**2 - (ax - straight) ** 2)


def trough_wall_gap(L, slide):
    """Smallest horizontal gap between the lift trough's outer surface and the
    basin wall, over every part of the trough that is below the basin rim."""
    d, n = np.array([C, 0, S]), np.array([-S, 0, C])
    best = 1e9
    for s in np.linspace(TAIL_S, TAIL_S + 400, 200):
        axis = L["origin_tail"] + d * s
        pts = [(R_OUT * math.sin(ph), -R_OUT * math.cos(ph)) for ph in np.linspace(-math.pi / 2, math.pi / 2, 37)]
        pts += [(sx * R_OUT, h) for sx in (-1, 1) for h in np.linspace(0, RIM_ABOVE_AXIS, 4)]
        for across, up in pts:
            p = axis + np.array([0, across, 0]) + n * up
            if p[2] > BASIN_RIM + 1:
                continue
            xr, yr = p[0] - slide["basin_cx"], p[1] - slide["basin_cy"]
            best = min(best, basin_limit(xr) - abs(yr))
    return best


def slide_layout(L):
    """Place the rigid slide chain alongside the lift (world x decreasing toward
    the basin) and work out riser heights so its far end spills over the rim."""
    x_start = L["O"][0] + L["spout_end_x"] + SPOUT_INSERT      # open top end of the first piece
    h0 = L["spout_floor_world_z"] - TRACK_FLOOR - SPOUT_DROP   # underside at the top end
    total = sum(n for _, n in SLIDE_CHAIN)
    h_end = BASIN_RIM + SLIDE_CLEAR_RIM
    slope = (h0 - h_end) / total
    risers, d = [], 0.0
    risers.append(["top end", round(h0 - slope * 15), x_start - 15])
    for name, length in SLIDE_CHAIN[:-1]:
        d += length
        if (x_start - d) < risers[-1][2] - 40:
            risers.append([f"joint after {name}", round(h0 - slope * d), x_start - d])
    # basin geometry: tail sits BASIN_TAIL_GAP from the wall; lift and slide straddle the centre
    tail_low_x = L["origin_tail"][0] + R_OUT * S
    chord = BASIN_HALF_IN
    basin_cx = tail_low_x - BASIN_TAIL_GAP + BASIN_HALF_IN
    end_x = x_start - total
    # extra support just outside the basin rim if the last piece overhangs a long way
    rim_x = basin_cx + BASIN_HALF_OUT + 40
    if risers[-1][2] - rim_x > 60 and rim_x > end_x:
        risers.append(["outside basin rim", round(h0 - slope * (x_start - rim_x)), rim_x])
    risers = [tuple(r) for r in risers]
    return dict(x_start=x_start, h0=h0, h_end=h_end, slope=slope, total=total, risers=risers,
                basin_cx=basin_cx, basin_cy=BASIN_CENTER_Y, chord=chord, end_x=end_x,
                tail_xr=tail_low_x - basin_cx)


# ------------------------------------------------------------------- checks
def check(name, m, report, print_oriented=True):
    st = m.status()
    b = m.bounding_box()
    size = (b[3] - b[0], b[4] - b[1], b[5] - b[2])
    fits = all(s <= BED for s in size)
    ok = st == mf.Error.NoError and m.volume() > 0 and fits
    report.append(f"| {name} | {size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f} | {m.volume()/1000:.0f} cm³ | "
                  f"{'yes' if fits else '**NO**'} | {'ok' if ok else '**FAIL**'} |")
    return ok


def build_geometry(extra_risers=()):
    """Build every part. Returns (parts in part frame, parts placed in world, layout, slide)."""
    L = layout()
    parts, world = {}, {}
    seg = screw_segment()
    parts[f"screw_segment_x{N_SEG}"] = seg
    for k in range(N_SEG):
        world[f"seg{k}"] = place(seg.translate((0, 0, k * PITCH)), L["origin_tail"])
    hub = drive_hub()
    parts["drive_hub"] = hub
    world["hub"] = place(hub.translate((0, 0, N_SEG * PITCH)), L["origin_tail"])

    n_tr = math.ceil((L["trough_top_s"] - TAIL_S) / TROUGH_MAX_PIECE)
    cuts = np.linspace(TAIL_S, L["trough_top_s"], n_tr + 1)
    for k in range(n_tr):
        piece, s0 = trough(cuts[k], cuts[k + 1], tail=(k == 0))
        name = f"trough_{k + 1}_of_{n_tr}" + ("_tail" if k == 0 else "_top" if k == n_tr - 1 else "")
        parts[name] = piece
        world[name] = place(piece.translate((0, 0, s0)), L["origin_tail"])

    hb = head_box(L)
    mm = motor_mount(L)
    world["head_box"] = hb.translate(tuple(L["O"]))
    world["motor_mount"] = mm.translate(tuple(L["O"]))
    parts["head_box"] = hb
    # motor mount prints with the wall plate flat on the bed
    parts["motor_mount"] = mm.rotate((0, -90, 0))
    parts["motor_hood"] = motor_hood()
    # stand footprint = head-box floor footprint (world-relative to O), slightly inset
    fx0 = L["hb_front_floor_x"] - HB_WALL / C - (HB_FLOOR) * S / C
    foot = (fx0 + 2, -HB_INNER_W / 2 - HB_WALL, L["hb_back_x"] + HB_WALL, HB_INNER_W / 2 + HB_WALL)
    stand = head_box_stand(L, foot)
    parts["head_box_stand"] = stand
    world["head_box_stand"] = stand.translate((L["O"][0], 0, 0))
    slide = slide_layout(L)
    for h in sorted(set([r[1] for r in slide["risers"]] + [round(x) for x in extra_risers])):
        parts[f"riser_{int(h)}mm"] = riser(h, slide["slope"])
    for (label, h, x) in slide["risers"]:
        world[f"riser@{x:.0f}"] = riser(h, slide["slope"]).rotate((0, 0, 90)).translate((x, SLIDE_OFFSET_Y, 0))

    return parts, world, L, slide


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--risers", type=float, nargs="*", default=[], help="extra riser heights (mm)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    parts, world, L, slide = build_geometry(args.risers)
    rep = ["| Part | Print size (mm) | Volume | Fits P1S | Solid |", "|---|---|---|---|---|"]

    all_ok = True
    for name, m in parts.items():
        m = to_bed(m)
        all_ok &= check(name, m, rep)
        write_stl(m, OUT / f"{name}.stl")
    asm = M()
    for m in world.values():
        asm += m
    write_stl(asm, OUT / "_assembly.stl")

    # ---------------------------------------------------- engineering checks
    flight_angle = math.degrees(math.atan(PITCH / (2 * math.pi * SCREW_R)))
    pocket_radial = SCREW_R - CORE_R
    pocket_axial = PITCH - FLIGHT_W
    flight_tip_t = FLIGHT_W * math.sin(math.radians(flight_angle))
    lift = N_SEG * PITCH * S
    ab = asm.bounding_box()
    rod_lo = TAIL_S + 1.5                             # bottom of the blind hole in the tail boss
    rod_hi = L["front_s"] + L["boss_face_s_rel"] + MOTOR_STANDOFF - COUPLER_LEN / 2 + 2
    rod_len = rod_hi - rod_lo
    # basin clearance: horizontal run from tail lowest point to where the trough underside clears the rim
    clear_run = (BASIN_RIM + 2 - BASIN_FLOOR_TOP) / math.tan(TH)
    trough_gap = trough_wall_gap(L, slide)
    spill_y = SLIDE_OFFSET_Y - BASIN_CENTER_Y
    spill_gap = min(basin_limit(slide["end_x"] - slide["basin_cx"] + t) - (abs(spill_y) + HB_SPOUT_W / 2)
                    for t in np.linspace(-20, 20, 9))
    area = math.pi * (SCREW_R**2 - CORE_R**2)
    q_geo = area * PITCH / 1e6  # litres per rev, geometric
    checks = [
        ("Incline below flight angle at screw tip", f"{INCLINE_DEG:.1f}° < {flight_angle:.1f}°", INCLINE_DEG < flight_angle - 2),
        ("Screw-to-trough radial clearance", f"{TROUGH_CLEAR:.1f} mm", 1.5 <= TROUGH_CLEAR <= 3),
        ("Pocket radial depth vs Floaty (largest side)", f"{pocket_radial:.0f} mm vs {max(FLOATY):.0f} mm", pocket_radial > max(FLOATY) + 5),
        ("Pocket axial gap vs Floaty", f"{pocket_axial:.0f} mm", pocket_axial > 2 * max(FLOATY)),
        ("Flight normal thickness at tip", f"{flight_tip_t:.1f} mm", flight_tip_t >= 2.4),
        ("Head-box spout fits inside track", f"{HB_SPOUT_W + 8:.0f} mm outer vs {TRACK_INNER_W:.0f} mm", HB_SPOUT_W + 8 < TRACK_INNER_W),
        ("Trough clears basin rim within basin", f"needs {clear_run:.0f} mm run, basin inside {2 * BASIN_HALF_IN - BASIN_TAIL_GAP:.0f} mm",
         clear_run < 2 * BASIN_HALF_IN - BASIN_TAIL_GAP - 10),
        ("Slide track clears the lift trough side by side",
         f"track inner edge {SLIDE_OFFSET_Y - 70.5:.0f} mm vs trough flange {R_OUT + FLANGE_W:.0f} mm from axis",
         SLIDE_OFFSET_Y - 70.5 > R_OUT + FLANGE_W + 2),
        ("Lift trough stays inside the basin outline until it clears the rim",
         f"min wall gap {trough_gap:.1f} mm", trough_gap >= 2.0),
        ("Slide spill stream lands inside the basin outline",
         f"end {slide['end_x'] - slide['basin_cx']:+.0f} mm from centre; stream edge gap {spill_gap:.1f} mm", spill_gap >= 3.0),
        ("Slide slope", f"{math.degrees(math.atan(slide['slope'])):.1f}° ({slide['slope']*100:.0f}%)", slide["slope"] > 0.01),
    ]
    rep2 = ["| Check | Value | Pass |", "|---|---|---|"]
    for n, v, p in checks:
        rep2.append(f"| {n} | {v} | {'yes' if p else '**NO**'} |")
        all_ok &= p
    facts = [
        ("Screw lift (axis rise over screw)", f"{lift:.0f} mm"),
        ("Trough tail axis height above table", f"{L['axis_tail_z']:.0f} mm"),
        ("Screw bottom above Big basin floor", f"{L['axis_tail_z'] - SCREW_R - BASIN_FLOOR_TOP:.0f} mm"),
        ("Recommended basin water level above table", f"{L['axis_tail_z'] - 10:.0f}-{L['axis_tail_z']:.0f} mm (axis height or slightly below)"),
        ("Head-box floor / spout lip above table", f"{L['spout_floor_world_z']:.0f} mm"),
        ("Head-box stand height", f"{L['hb_base_world_z']:.0f} mm"),
        ("First slide track underside at its top end", f"{L['spout_floor_world_z'] - TRACK_FLOOR - SPOUT_DROP:.0f} mm"),
        ("Slide end must clear basin rim (underside)", f"≥ {BASIN_RIM + 3:.0f} mm"),
        ("Fall available for the slide", f"{L['spout_floor_world_z'] - TRACK_FLOOR - SPOUT_DROP - (BASIN_RIM + SLIDE_CLEAR_RIM):.0f} mm"),
        ("Stainless rod length (cut)", f"{rod_len:.0f} mm (buy 6 x {math.ceil((rod_len + 20) / 100) * 100:.0f} mm)"),
        ("Lift footprint (assembly bbox)", f"{ab[3]-ab[0]:.0f} x {ab[4]-ab[1]:.0f} x {ab[5]-ab[2]:.0f} mm"),
        ("Geometric pocket volume", f"{q_geo:.2f} L/rev (real delivery ~20-30% of this)"),
        ("Est. delivery at 40 rpm", f"{q_geo*40*0.2:.1f}-{q_geo*40*0.3:.1f} L/min"),
    ]
    facts += [
        ("Basin placement", f"Big basin centre {BASIN_CENTER_Y:.0f} mm to the slide side of the lift axis; "
                            f"trough tail {BASIN_TAIL_GAP:.0f} mm from the wall behind it"),
        ("Head-box spout (rim of pour tip) above track floor", f"{TIP_LIFT + 1:.0f} mm at the entry"),
        ("Slide chain (top → bottom)", " → ".join(n for n, _ in SLIDE_CHAIN) + f" ({slide['total']:.0f} mm)"),
        ("Slide underside, top end / spill end", f"{slide['h0']:.0f} mm / {slide['h_end']:.0f} mm"),
    ]
    rep3 = ["| Quantity | Value |", "|---|---|"] + [f"| {a} | {b} |" for a, b in facts]
    rep4 = ["| Riser | Position | Height (table → track underside) | STL |", "|---|---|---|---|"]
    for label, h, x in slide["risers"]:
        rep4.append(f"| {label} | {slide['x_start'] - x:.0f} mm from the slide's top end | {h} mm | `riser_{h}mm.stl` |")
    text = ["# Generated lift report", "", "Produced by `cad/lift/build.py`; do not edit by hand.", "",
            "## Parts", "", *rep, "", "## Design checks", "", *rep2, "", "## Layout numbers", "", *rep3, "",
            "## Slide risers", "", *rep4, ""]
    (OUT / "REPORT.md").write_text("\n".join(text))
    print("\n".join(text))
    print("ALL OK" if all_ok else "SOME CHECKS FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
