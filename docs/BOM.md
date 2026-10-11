# Bill of materials

## Printed

| Item | Qty | Source |
|---|---|---|
| I (straight track) | 2 | HydroLink 3MF, plate "I" |
| Big basin | 1 | HydroLink 3MF, plate "Big basin" |
| Sealing insert | 2 + one per End cap | HydroLink 3MF, plate "Sealing insert" |
| Clamps V2 | per joint (2 slide joints + End caps) | HydroLink 3MF, plate "Clamps V2" |
| End cap | one per unused basin port | HydroLink 3MF, plate "End cap" |
| Flow modifier_body | 1 | FlowLab 3MF |
| Flow modifier (filter variant) | 1 | FlowLab 3MF, plate "Flow modifier" |
| Floaty | 10 | FlowLab 3MF |
| Screw segment | 4 | `cad/lift/stl/screw_segment_x4.stl` |
| Drive hub | 1 | `cad/lift/stl/drive_hub.stl` |
| Trough pieces | 3 | `trough_1_of_3_tail`, `trough_2_of_3`, `trough_3_of_3_top` |
| Head box | 1 | `head_box.stl` |
| Head box stand | 1 | `head_box_stand.stl` |
| Motor mount | 1 | `motor_mount.stl` |
| Motor hood | 1 | `motor_hood.stl` |
| Slide risers | 3 | `riser_183mm`, `riser_133mm`, `riser_106mm` |

Filament: PETG, roughly 1.5–2.5 kg for the new lift parts at 4 walls / 15% gyroid. The new parts total about 2.0 L of solid volume (see `cad/lift/stl/REPORT.md`), and infill reduces that.

## Mechanical hardware

| Item | Qty | Notes |
|---|---|---|
| Stainless steel rod, 6 mm | 1 | **cut to 741 mm**; buy 800 mm. 304 or 316 so it doesn't rust. |
| 686ZZ bearing (6 × 13 × 5 mm) | 1 | head-box back wall |
| Flexible shaft coupler, 4 mm → 6 mm, ~Ø19 × 25 mm | 1 | motor shaft to rod |
| M3 × 16 socket screw + nut | 17 | 8 for the trough flanges, 4 for head box ↔ trough, 4 for the motor mount, 1 for the clamp |
| M3 grub screw, 6 mm | 1 | drive hub; tap the 2.5 mm hole M3 |
| Silicone tube, 6 mm OD / 4 mm ID | ~2 m | **required** by the HydroLink seal system (vinyl won't seal) |
| Aquarium-safe silicone sealant | 1 tube | lift trough flanges and head-box joint |

## Electrical (all 5 V DC)

| Item | Qty | Notes |
|---|---|---|
| Gear motor JGA25-370, **6 V, 40–60 rpm** | 1 | run at 5 V; needs at least 3 kg·cm torque; 25 mm gearbox, 4 mm D-shaft |
| PWM DC motor speed controller, 5 V, ≥1 A | 1 | for tuning the screw speed |
| USB 5 V 2 A supply + USB cable with bare leads (or a USB-C PD trigger set to 5 V) | 1 | |
| Resettable fuse (polyfuse) 1 A | 1 | in series with the motor |
| Inline switch (optional) | 1 | |
| Heat-shrink, zip ties | | drip loop and strain relief |
