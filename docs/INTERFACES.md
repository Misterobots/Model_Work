# Interfaces with the HydroLink and FlowLab files

These numbers were taken directly from the meshes in `HydroLink_final_V1.33.3mf` and `FlowLab3.3mf`. Re-run `cad/tools/measure_hydrolink.py` to reproduce them. The 3MF files are not stored in this repo.

## Your original plan vs. what the files contain

| Original plan calls for | In the files? | Used instead |
|---|---|---|
| Straight tracks | Yes: **I**, 141 × 70 × 200 | I ×2 |
| 45° / 90° curves | 90° only (**Elbow**, 170.5 × 170.5); **no 45° part** | not needed in the default layout |
| Medium / Big basin | both | **Big basin**. The Medium basin is too small: the trough needs ~146 mm to rise over the rim, plus 80 mm behind the tail. |
| V2 Locking Clamps | Clamps V2 (18 × 70 × 51.6) | as is |
| Archimedes screw shaft, outer tube, flanged mounts | **No.** The HydroLink Pump Station is hand-powered and a separate release. | **new parts** in `cad/lift/` |
| Sliding gates | **No.** Flow blocker (131 × 75.5 × 18) is a drop-in slab. | **Flow modifier body + filter** as the staging gate |
| Vortex / funnel connectors | Flow chamber 213 × 70 × 230, Vortex insert (~22 mm centre drain), I Adapter 141 × 70 × 170; no funnel | not in the default loop (see BUILD_GUIDE §7) |
| Vinyl tubing | System seals with **6/4 mm silicone tube** + sealing inserts | silicone tube for seals; no return tube is needed with the screw lift |

## Measured interface numbers

| Feature | Value | Used for |
|---|---|---|
| Track outer section (mid-length) | 125 wide × 70 tall | slide / lift side-by-side clearance |
| Track flange zone | last 10 mm at each end, 141 wide | clamps; pour-tip insert depth |
| Track inner floor | 9.5 mm above the track underside | riser heights, spout drop |
| Track channel profile | rounded U, 18.7 wide at 1 mm, 47.5 at 5 mm, 89 at 20 mm, 121 at 60 mm | pour tip shape (`TRACK_PROFILE`) |
| Seal ridge in the track end zone | ~6.5 mm above the channel floor | pour tip rides 7 mm above the floor (found by `check_fit.py`) |
| Big basin | 250 × 250 × 70 rounded square, ~2 mm walls, corner radius ~69 mm | lift tail and slide spill placement |
| Big basin floor top | 13 mm above the table (Medium: 9.6 mm) | screw tail height |
| Floaty | 20 × 20 × 18.5 | screw pocket size |
| Vortex insert drain | ~22 × 22 mm | Floaties (20 mm) are a near fit |
| Flow blocker / Flow modifier body | 131 × 75.5 × 18 | staging-gate joint |
| Printer profile in both files | Bambu Lab P1S (256 mm bed) | every new part is checked to fit |

## What has been verified against the real meshes (`cad/tools/check_fit.py`)

The checker places the actual Big basin, two I tracks and the Flow modifier body in the generated layout and boolean-intersects them with every new part. The result is in `cad/lift/stl/FIT_REPORT.md`.

- **Pour tip vs I track:** 0.00 cm³. The tip sits inside the channel without touching, including the seal ridge.
- **Lift trough vs Big basin:** no collision, including the rounded corners. The tail rests on the floor.
- **Risers vs tracks:** surface contact only (≤ 0.2 cm³ from the tilted pads). Every riser carries the slide (within 1.5 mm).
- **Slide spill end:** over the basin interior, 77 mm underside (rim 70 mm).

The checker caught and fixed four real problems during design:
- the flat spout hit the rounded channel
- the spout hit the seal ridge
- an outboard tail bracket and riser hit the basin wall
- the trough's tilted tail face hit the basin's rounded corner

## Not verifiable from the meshes (dry-fit list)

See BUILD_GUIDE §8. The main ones:
- how the Flow modifier body seats in a joint
- basin port positions
- the screw incline vs flight angle with real water
