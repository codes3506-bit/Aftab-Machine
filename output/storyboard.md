# Storyboard: Khabri-1 Hill Post, Track Options (final cut, 2:00)

3840×2160 native, 30 fps (plus a 1080p export). **All five options get equal treatment. There is no recommendation, ranking or weighted score.**

Look and type:
- One grade for the 3D and the drone footage. 3D is rendered natively at 4K from Esri 0.6 m imagery on Cop GLO-30 (VE 1.0), with a crispening and clarity pass.
- Type: Inter / Inter Display, with JetBrains Mono for live figures. Each option has its own colour; none carries the gold accent.

Camera:
- All moves use Catmull-Rom splines with smootherstep easing. There are no linear moves.
- The fly-throughs follow each track from about 520 m behind and 430 m above, so imagery detail matches 4K.
- There is a 0.5 s dissolve at every cut.

| # | TC | Picture | Camera | On screen | Audio |
|---|---|---|---|---|---|
| 1 | 0:00–0:08 | Drone 00:37–00:45, Taloband Rg S face, letterboxed 2.39:1 | slow 7 % push-in | Title **TRACK RECCE · OPTIONS / KHABRI-1 HILL POST**. Geotag chip `DRONE 00:xx · ASSESSED` | wind, pad |
| 2 | 0:08–0:20 | 3D establishing; opens on the drone's heading | orbit S → SW, descending | Post pin with grid and RL. AOI draws on. KMZ track draws on. T4 take-off CH tag (computed) | woosh, pin chime |
| 3 | 0:20–0:30 | Slope tint (2 km corridor) then drainage | lateral truck from SE | Slope legend; S face ≈ 22° and N face ≈ 24° (mean slope within 250 m, computed from Cop GLO-30) | data scan |
| 4 | 0:30–0:40 | DEM N–S section through the post (true profile only, no drawn bedding) + drone 00:58–01:08 | locked | Computed face slopes. Bedding on both faces, so beds gently dipping (**ASSESSED**) | low hit |
| 5 | 0:40–0:55 | T1→T5 draw on one by one (2.6 s each) and stay | slow 38° orbit | Tags and legend | sparkle per track; riser |
| 6–10 | 0:55–1:45 | **Option flights:** T1, T2, T3, T4, T5, 10 s each | elevated chase along each track, ends looking at the post | Live CH / ELEV / GRADE; per-option card (length, grades, hairpins, nala xings, cut, exposure, POL, work days, profile) | impact at 0:55 (only full-frame hit); swoosh per option |
| 11 | 1:45–1:54 | Plan view, N up, labelled tracks + factual table + column key | 4 % push | No scores, no radar, no ranking. Footnote on accuracy | table ticks |
| 12 | 1:54–2:00 | **OPTIONS FOR DECISION:** five equal columns of figures | static, fade out | "All alignments are least-cost corridors on a 30 m DEM · figures assessed · confirm by gr recce before pegging" | aura, resolve |

Every on-screen figure is read from `work/metrics.json` and `pol.json`, or computed from the DEM at render time (face slopes, DSM bias). The only literal inputs are the post RL 133 and its coordinates, both given by the user. Cut is shown on the same basis as POL (incl the KMZ new tr portion). `mcda.json` is not used in the film.
