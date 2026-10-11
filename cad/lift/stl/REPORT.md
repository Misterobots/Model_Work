# Generated lift report

Produced by `cad/lift/build.py`; do not edit by hand.

## Parts

| Part | Print size (mm) | Volume | Fits P1S | Solid |
|---|---|---|---|---|
| screw_segment_x4 | 90 x 90 x 143 | 82 cm³ | yes | ok |
| drive_hub | 24 x 24 x 18 | 6 cm³ | yes | ok |
| trough_1_of_3_tail | 120 x 69 x 185 | 149 cm³ | yes | ok |
| trough_2_of_3 | 120 x 68 x 185 | 153 cm³ | yes | ok |
| trough_3_of_3_top | 120 x 68 x 185 | 153 cm³ | yes | ok |
| head_box | 193 x 248 x 151 | 595 cm³ | yes | ok |
| motor_mount | 78 x 64 x 71 | 80 cm³ | yes | ok |
| motor_hood | 37 x 37 x 80 | 19 cm³ | yes | ok |
| head_box_stand | 130 x 128 x 201 | 160 cm³ | yes | ok |
| riser_106mm | 100 x 70 x 110 | 106 cm³ | yes | ok |
| riser_133mm | 100 x 70 x 137 | 124 cm³ | yes | ok |
| riser_183mm | 100 x 70 x 187 | 157 cm³ | yes | ok |

## Design checks

| Check | Value | Pass |
|---|---|---|
| Incline below flight angle at screw tip | 22.0° < 25.5° | yes |
| Screw-to-trough radial clearance | 2.0 mm | yes |
| Pocket radial depth vs Floaty (largest side) | 33 mm vs 20 mm | yes |
| Pocket axial gap vs Floaty | 129 mm | yes |
| Flight normal thickness at tip | 2.6 mm | yes |
| Head-box spout fits inside track | 98 mm outer vs 120 mm | yes |
| Trough clears basin rim within basin | needs 146 mm run, basin inside 166 mm | yes |
| Slide track clears the lift trough side by side | track inner edge 64 mm vs trough flange 60 mm from axis | yes |
| Lift trough stays inside the basin outline until it clears the rim | min wall gap 5.3 mm | yes |
| Slide spill stream lands inside the basin outline | end +45 mm from centre; stream edge gap 5.2 mm | yes |
| Slide slope | 15.3° (27%) | yes |

## Layout numbers

| Quantity | Value |
|---|---|
| Screw lift (axis rise over screw) | 202 mm |
| Trough tail axis height above table | 60 mm |
| Screw bottom above Big basin floor | 2 mm |
| Recommended basin water level above table | 50-60 mm (axis height or slightly below) |
| Head-box floor / spout lip above table | 207 mm |
| Head-box stand height | 197 mm |
| First slide track underside at its top end | 187 mm |
| Slide end must clear basin rim (underside) | ≥ 73 mm |
| Fall available for the slide | 114 mm |
| Stainless rod length (cut) | 741 mm (buy 6 x 800 mm) |
| Lift footprint (assembly bbox) | 737 x 251 x 372 mm |
| Geometric pocket volume | 0.80 L/rev (real delivery ~20-30% of this) |
| Est. delivery at 40 rpm | 6.4-9.6 L/min |
| Basin placement | Big basin centre 63 mm to the slide side of the lift axis; trough tail 80 mm from the wall behind it |
| Head-box spout (rim of pour tip) above track floor | 7 mm at the entry |
| Slide chain (top → bottom) | I → Flow modifier body + filter (staging gate) → I (418 mm) |
| Slide underside, top end / spill end | 187 mm / 73 mm |

## Slide risers

| Riser | Position | Height (table → track underside) | STL |
|---|---|---|---|
| top end | 15 mm from the slide's top end | 183 mm | `riser_183mm.stl` |
| joint after I | 200 mm from the slide's top end | 133 mm | `riser_133mm.stl` |
| outside basin rim | 298 mm from the slide's top end | 106 mm | `riser_106mm.stl` |
