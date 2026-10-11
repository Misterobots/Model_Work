# Automated 5V HydroLink Mini Water Slide: interface check and revised plan

Sources checked: `HydroLink_final_V1.33.3mf` (12 plates) and `FlowLab3.3mf` (8 plates). Meshes were measured directly; the designers' descriptions and photos were read. "Measured" below means taken from the mesh; "estimate" means calculated or inferred and needs a dry-fit to confirm.

## 1. What the attached files do and don't contain

| Your plan calls for | In the files? | What to use instead |
|---|---|---|
| Straight tracks | Yes: **"I"** (measured 141 x 70 x 200 mm) | as is |
| 45° and 90° curves | **Only 90°**: **"Elbow"** (170.5 x 170.5) | no 45° part exists; plan on 90° elbows only |
| Medium / Big basin | Yes: Medium (202 x 200), Big (250 x 250) | as is |
| V2 Locking Clamps | Yes: "Clamps V2", 4 per plate (18 x 70 x 51.6) | as is |
| Sealing inserts | Yes (7 per plate, 133 x 66.5 x 4); you didn't list them, but the system **requires** them | add to the BOM |
| End cap | Yes (20 x 70 x 141) | solid plug; the tube-port version below is a new part |
| **Archimedes screw pump station, outer tube, flanged mounts** | **No.** The HydroLink description says its Pump Station is *hand-powered* and a separate release | design a new motor-driven lift (section 3) |
| **Sliding Gates** | **No.** The closest is **"Flow blocker"** (131 x 75.5 x 18), a drop-in slab, not a sliding gate | use the Flow blocker; confirm its slot when dry-fitting |
| **Vortex / Funnel connectors** | Partly: FlowLab has **Flow chamber** (213 x 70 x 230), a **Vortex insert** with a ~22 mm centre drain (estimate from the mesh), and an **I Adapter** (141 x 70 x 170). There is no funnel connector. | use chamber + insert + I Adapter; a funnel adapter is a new part |
| Vinyl tubing | The system seals joints with **6 mm OD / 4 mm ID silicone tube** plus the sealing inserts. Vinyl is too stiff and won't seal. | silicone tube for seals only |

## 2. Interface facts that drive the design

- **Channel:** half-pipe with inner radius about 60 mm (estimate from a mesh slice), about 120 mm wide and 60 mm deep. Flange face is 141 x 70 mm. Every joint is a flange face + sealing insert + silicone tube + V2 clamps.
- **Tracks are level modules.** The files include no sloped track, so the slide's fall has to come from tilting the whole assembled run (the designer calls the joints rigid) on printed 4° wedge feet. That gives about 14 mm of drop per 200 mm track.
- **Floaty (FlowLab):** 20 x 20 x 18.5 mm, hollow (2 walls, 0% infill). Your minis should be similar in size, and the lift has to carry them. Floaties are sized to be blocked by the FlowLab filter, so an impeller path is a jam risk.
- **Print profiles in the files:** HydroLink uses 3 walls, 10% gyroid, 0.2 mm layers, clamps at 8 walls; FlowLab uses 0.12 mm layers. Your 4 walls / 15% gyroid is compatible and stronger, so keep it. Printer profile is Bambu P1S, 256 mm bed.
- **Leak-proof is not achievable as stated.** The designer says it is for *outdoor use* and that "small leaks are possible due to the modular design". Mitigations in this plan:
  - sealing inserts and 6/4 silicone tube at every joint
  - 4 walls on all water-contact parts
  - the whole run built inside a sink or a shallow tray, so any leak drains back
  - a dry-paper water test before any electronics go near it

## 3. Lift: recommended design

**Recommendation: an inline, motor-coaxial Archimedes screw in an open, inclined trough.**

- **Why:** it is the only lift option that carries water **and** the floating minis in one step. A printed impeller pump with a tube moves water only, so minis pile up in the basin and have to be restaged by hand. Impellers can also jam on a mini or a Floaty.
- **Why the motor can be inline and dry:** the motor sits on the same axis as the screw, at the **top, above the water**. No shaft seal is needed, which removes the usual failure point of a printed pump with a wet motor.
- **Fallback (Option B):** if you want a true pump, use a printed volute for a sealed submersible 5V pump, with the FlowLab fine filter in front and silicone tube up to the top end-cap. Minis would then not be lifted. I'd only take this if you accept restaging them by hand.

### Screw parameters (starting values)

| Item | Value | Basis |
|---|---|---|
| Outer diameter D | 90 mm | fits a trough with inner R 47 mm, 2 mm clearance |
| Core diameter | 24 mm, with 6 mm axial bore for a stainless rod | |
| Pitch | 135 mm (1.5 x D) | |
| Flight pitch angle at the outer edge | about 25.5° | atan(135 / (π x 90)) |
| Trough incline | **22°** | kept below the flight angle so the pockets hold water; **confirm on the first prototype segment** |
| Pocket radial depth | 33 mm | carries 20 mm Floaties and about 30 mm minis |
| Length | 3 segments x 135 mm (one turn each), about 405 mm | |
| Lift height | about 150 mm | 405 x sin 22° |
| Flow estimate | 2-5 L/min at about 40 rpm | rough estimate; to be bench-measured |
| Print | flight 3.2 mm (solid), 4 walls, supports needed (flight tips are an overhang); each segment fits the bed upright | |

### Drive

- Gear motor: 25GA-370 (or similar) rated 6V, 40-60 rpm, run at 5V, with a 4 mm D-shaft.
- Printed bracket at the top holds the motor, a bearing, and a splash cover.
- A flexible coupler joins the motor shaft to a 6 mm x about 440 mm stainless rod through all three segments.
- A printed wet bushing cup holds the rod at the bottom end.
- Power: 5V 2A USB supply, 1 A resettable fuse, a PWM speed module for tuning, and a drip loop on the cable.
- Estimated load is under 1 W hydraulic. Friction dominates, so choose a motor with at least 3 kg·cm torque.

### New parts to model (everything else is from your files)

1. Screw segments x 3 (keyed joints, rod bore).
2. Lift trough, two halves, inner R 47 mm, with a HydroLink-style flange at the top end.
3. Top bearing and motor bracket with splash cover.
4. Bottom bushing cup and sump sleeve.
5. Funnel adapter: R 47 mm trough to the 141 x 70 HydroLink flange, with a sealing-insert recess.
6. End cap with a cable pass-through is optional; there is no tube port in this version.
7. 4° wedge feet for the slide.

## 4. Revised assembly

**Phase A: Lift**
1. Print and fit the screw segments on the rod.
2. Dry-spin them in the trough by hand and confirm no rubbing.
3. Mount the motor bracket at the top.
4. Wet-test the lift on its own in a tray before connecting anything else.

**Phase B: Slide run (top to bottom)**

Lift top, then funnel adapter, then FlowLab **I Adapter**, then **Flow blocker** (staging gate), then I / Elbow tracks. This replaces your step 1, because the Flow blocker is a drop-in slab, not a sliding gate. Seal every joint with sealing insert + silicone tube + V2 clamps. Tilt the whole run about 4° on the wedge feet.

**Phase C: Return loop**
1. The lowest track feeds the FlowLab **Flow chamber** with the **Vortex insert**.
2. The chamber outlet goes into the **Medium basin**.
3. The screw's tail sits in the basin sump. Keep at least 40 mm of the tail submerged at the basin's water level (estimate; confirm at dry-fit).
4. There is no vinyl return tube, so the "route tube up the tower" step is dropped.

## 5. Open items to confirm at dry-fit

These could not be settled from the meshes alone:
- the Flow blocker's slot location (which FlowLab part it drops into)
- whether the Vortex insert's centre drain needs its own outlet path or the chamber side port is enough
- the basin water level versus the port sill
- the exact inner radius and flange details of the track end-face
- the incline versus pocket retention (the 22° vs 25.5° check)

## 6. What I will produce on approval

- `docs/BUILD_GUIDE.md`: your original text rewritten against the real part names above.
- `cad/lift/`: a parametric generator script plus STL files for the new parts in section 3 (untested until printed).
- `docs/interfaces.md` and a small script that recomputes the fit checks from the measurements.
- `docs/BOM.md`.
- The 3MF files are **not** committed (25 MB); they are referenced by name.
