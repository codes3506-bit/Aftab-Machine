# DRONE TRG COMPLEX - 44 DIV

3D design of the drone training complex at **GR 25°19'47.62"N 62°30'33.00"E**, built as a native
SketchUp model on the real terrain, plus a 1080p fly-through video rendered from the same design.

| Deliverable | Where |
|---|---|
| SketchUp model (`.skp`, 8 scenes, geo-located) | `deliverables/Drone_Trg_Complex_44_Div.skp` (download link in the session) |
| Video, 1920x1080, 30 fps, with soundtrack | `deliverables/Drone_Trg_Complex_44_Div.mp4` |
| Stills / SketchUp thumbnail | `deliverables/` |

## The design

The building faces **north**; the GR is the centre of the building. No labels anywhere except the
title **DRONE TRG COMPLEX - 44 DIV**, built as solid 3D letters from the genuine **Arial Bold**
outlines on the top front parapet.

**Drone concept.** The four corner towers are the drone's rotor pods: each carries a finned
motor housing, a 11 m two-blade carbon propeller with orange tips, and a guard ring. Carbon arms run
from a flight-controller hub on the roof (with GPS mast, antennas, gimbal camera and blue LED ring)
out to each motor, so from above the complex reads as a quadcopter. Nav lights: red on the front
pods, green on the rear. In the video the propellers spin counter-rotating pairs and spool up with
a dust swirl in the take-off shot.

**Inside (floor level 0.3 m, ceiling 5.4 m):**

| Area | Contents |
|---|---|
| Lecture hall (west) | Raised stage with lectern, panel table and 3 chairs, 8.2 m projection screen, curtains, speakers; **60 tiered padded seats** (6 rows x 10, centre aisle); acoustic timber slats; AV desk |
| Foyer (centre) | Reception desk with LED strip, display quadcopter on a lit plinth, fixed-wing UAV model, sofas, wall screen |
| Simulator complex (east) | **8 pilot stations** (triple monitors, RC transmitter, FPV goggles, racing seat), 3x2 video wall, instructor console, full-motion simulator pod on a hexapod |
| Rotor-pod rooms | NE drone workshop, SE battery charging racks, SW AV/server room, NW green room behind the stage |

**Site:** compound 110 x 92 m with boundary wall and north gate, roundabout with national flag,
lawns, parking with tactical vehicles, a **drone flying field** (4 race gates, 2 landing pads with
training quads, windsock), ground control station truck with dish, 18 m comms mast, street lights,
and an approach road draped on the terrain to the metalled road ~410 m west of the GR.

## Terrain analysis (real data)

Source: Copernicus GLO-30 DSM (30 m) and Esri World Imagery (z17, ~1 m/px). Script:
`terrain/fetch_terrain.py` -> `build/terrain.json`.

| Item | Value |
|---|---|
| Elevation at GR | 23.8 m |
| Pad (formation) level used | 23.4 m (median within 60 m) |
| Slope across the site | mean 2.1°, max 3.3° (falls to the east) |
| Relief within 100 m / 500 m / 1 km | 5.7 m / 9.0 m / 27.3 m |
| Ground over 10° within 1 km | 0.7 % |
| Highest point within 1.5 km | 47.6 m, 1.2 km at bearing 317° (NW) |
| Earthwork estimate for the pad (r 60 m) | cut ~7,500 m³, fill ~5,000 m³ |

The SketchUp terrain is a 1.8 x 1.8 km mesh (20 m grid, 16,200 faces) with the satellite image
mapped to it; the video uses 3 x 3 km at 20 m plus a 16 x 16 km backdrop. The ground under the
compound is flattened to the pad level and eased back into the real terrain over 45 m.

## How it is built

```
terrain/fetch_terrain.py    DEM + imagery download, local ENU grids, site analysis
design/make_glyphs.py       Arial Bold outlines -> polygons (glyphs_arialbd.py)
design/complex.py           parametric generator: the whole complex as prisms, lathes, meshes,
                            component definitions and instances (one source of truth)
sketchup/pack_spec.py       runs the generator + builds the terrain mesh, packs the JSON into a
                            lossless PNG (the SketchUp sandbox only accepts image uploads)
sketchup/adapter.py         runs inside SketchUp (build_model): decodes the payload, builds native
                            groups, component definitions/instances, lofted solids, UV-mapped terrain
render/export_spec.py       same generator -> spec.json + terrain binaries + real sun position
render/viewer.html          three.js renderer of the spec (open with ?base=../build/ for a preview)
render/timeline.js          shot list (9 shots); render_video.js renders frames via headless Chromium
render/audio.py, assemble.py  soundtrack, crossfades, final MP4
```

`complex.py` is written to run unchanged in the SketchUp sandbox and in CPython. Change a dimension
there and both the model and the video follow.

### Rebuild

```bash
python3 terrain/fetch_terrain.py
python3 render/export_spec.py
python3 sketchup/pack_spec.py           # then upload build/spec_payload.png and run adapter.py in SketchUp
node render/render_video.js build/video all
python3 render/audio.py && python3 render/assemble.py
```

Sun and shadows are set for the GR on 27 Nov 2026, 15:00 PKT (azimuth 220°, elevation 32°).
