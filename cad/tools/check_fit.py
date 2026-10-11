#!/usr/bin/env python3
"""Interface check against the real HydroLink / FlowLab meshes.

Places the actual Big basin, two "I" tracks and the FlowLab Flow modifier body
(staging gate) from the 3MF files into the generated lift layout, then measures
every overlap between the new parts and the HydroLink parts.

    python3 -I cad/tools/check_fit.py HydroLink_final_V1.33.3mf FlowLab3.3mf

Writes cad/lift/stl/FIT_REPORT.md and docs/img/fit_*.png. Nothing from the 3MF
files is written to the repo except these renders.
"""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import manifold3d as mf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from measure_hydrolink import Package  # noqa: E402

spec = importlib.util.spec_from_file_location("build", ROOT / "cad/lift/build.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

TOUCH = 1.0  # cm³ of overlap tolerated where parts are meant to rest on each other


def frame(u, v):
    """3x4 rotation whose columns map local (x across, y up, z along) to world."""
    w = np.cross(v, u)
    return np.column_stack([w, v, u])


def place_local(m, R, local_pt, world_pt):
    T = np.asarray(world_pt) - R @ np.asarray(local_pt)
    return m.transform(np.column_stack([R, T]).tolist())


def vol(a, b):
    return (a ^ b).volume() / 1000.0


def main(hydro, flow):
    H, F = Package(hydro), Package(flow)
    hp, fp = dict(H.plates()), dict(F.plates())
    parts, world, L, slide = B.build_geometry()
    a = math.atan(slide["slope"])
    u = np.array([-math.cos(a), 0.0, -math.sin(a)])      # down the slide
    v = np.array([-math.sin(a), 0.0, math.cos(a)])       # track "up"
    R = frame(u, v)
    y = B.SLIDE_OFFSET_Y
    p1 = np.array([slide["x_start"], y, slide["h0"]])     # underside of track 1 at its top end

    hl = {}
    track = H.solid(hp["I"][0])                           # CAD: x across, y up, z along (±100)
    hl["track_1"] = place_local(track, R, (0, -35, -100), p1)
    gate = F.solid(fp["Flow modifier_body"][0])           # 131 x 75.5 x 18
    gb = gate.bounding_box()
    p_gate = p1 + 200 * u
    hl["gate"] = place_local(gate, R, ((gb[0] + gb[3]) / 2, gb[1], gb[2]), p_gate)
    p2 = p1 + (200 + B.SLIDE_CHAIN[1][1]) * u
    hl["track_2"] = place_local(track, R, (0, -35, -100), p2)
    basin = H.solid(hp["Big basin"][0]).rotate((90, 0, 0))
    bb = basin.bounding_box()
    hl["big_basin"] = basin.translate((slide["basin_cx"] - (bb[0] + bb[3]) / 2, slide["basin_cy"] - (bb[1] + bb[4]) / 2, -bb[2]))

    lift_names = [k for k in world if not k.startswith("riser")]
    risers = {k: world[k] for k in world if k.startswith("riser")}
    rows, ok = [], True

    def row(what, value, good, note=""):
        nonlocal ok
        ok &= good
        rows.append(f"| {what} | {value} | {'yes' if good else '**NO**'} | {note} |")

    floor_z = B.BASIN_FLOOR_TOP + 2.0
    for h, hm in hl.items():
        for k in lift_names:
            x = world[k] ^ hm
            ov = x.volume() / 1000.0
            if ov > 0.001 or (h == "track_1" and k == "head_box"):
                top = x.bounding_box()[5] if ov > 0 else 0
                rest = h == "big_basin" and k.startswith("trough_1") and top <= floor_z
                row(f"`{k}` vs {h}", f"{ov:.2f} cm³ (up to z={top:.0f})", ov <= 0.001 or (rest and ov <= TOUCH),
                    "tail resting on basin floor" if rest else ("spout tip inside track 1" if k == "head_box" else "collision"))
    for k, r in risers.items():
        for h, hm in hl.items():
            ov = vol(r, hm)
            if ov > 0.001:
                row(f"`{k}` vs {h}", f"{ov:.2f} cm³", ov <= TOUCH and h != "big_basin", "track rests on riser" if h != "big_basin" else "")
    # every riser must actually carry the slide
    for k, r in risers.items():
        carried = any(len((hm ^ r.translate((0, 0, 1.5))).to_mesh().tri_verts) > 0 for hm in (hl["track_1"], hl["track_2"], hl["gate"]))
        row(f"`{k}` supports the slide", "contact within 1.5 mm" if carried else "gap > 1.5 mm", carried)
    # slide end lands over the basin interior, above the rim
    end = p2 + 200 * u
    d = math.hypot(end[0] - slide["basin_cx"], end[1] - slide["basin_cy"])
    row("Slide spill end over basin", f"{d:.0f} mm from basin centre, underside {end[2]:.0f} mm",
        B.basin_limit(end[0] - slide["basin_cx"]) - abs(end[1] - slide["basin_cy"]) > B.HB_SPOUT_W / 2 and end[2] > B.BASIN_RIM)
    report = ["# Interface fit report (real HydroLink meshes)", "",
              "Produced by `cad/tools/check_fit.py`; do not edit by hand.", "",
              "| Pair | Overlap / value | Pass | Note |", "|---|---|---|---|", *rows, "",
              "Overlap is the volume of the boolean intersection. Zero means the parts never touch.", ""]
    (ROOT / "cad/lift/stl/FIT_REPORT.md").write_text("\n".join(report))
    print("\n".join(report))

    # renders: lift + real HydroLink parts
    tmp = ROOT / "cad/lift/stl/_fit_scene.stl"
    scene = mf.Manifold()
    for m in list(world.values()) + list(hl.values()):
        scene += m
    B.write_stl(scene, tmp)
    import subprocess
    for view in ("iso", "top", "side"):
        subprocess.run([sys.executable, str(HERE / "render_stl.py"), str(ROOT / f"docs/img/fit_{view}.png"), str(tmp),
                        "--view", view, "--title", f"Lift + real HydroLink parts ({view})"], check=True)
    tmp.unlink()
    print("ALL FIT CHECKS PASS" if ok else "FIT PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
