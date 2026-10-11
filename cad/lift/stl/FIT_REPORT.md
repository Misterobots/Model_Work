# Interface fit report (real HydroLink meshes)

Produced by `cad/tools/check_fit.py`; do not edit by hand.

| Pair | Overlap / value | Pass | Note |
|---|---|---|---|
| `head_box` vs track_1 | 0.00 cm³ (up to z=0) | yes | spout tip inside track 1 |
| `riser@336` vs track_1 | 0.21 cm³ | yes | track rests on riser |
| `riser@336` vs gate | 0.01 cm³ | yes | track rests on riser |
| `riser@336` vs track_2 | 0.10 cm³ | yes | track rests on riser |
| `riser@238` vs track_2 | 0.05 cm³ | yes | track rests on riser |
| `riser@521` supports the slide | contact within 1.5 mm | yes |  |
| `riser@336` supports the slide | contact within 1.5 mm | yes |  |
| `riser@238` supports the slide | contact within 1.5 mm | yes |  |
| Slide spill end over basin | 93 mm from basin centre, underside 77 mm | yes |  |

Overlap is the volume of the boolean intersection. Zero means the parts never touch.
