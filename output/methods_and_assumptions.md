# Methods, data and accuracy limits

## Data
| Layer | Source | Resolution | Note |
|---|---|---|---|
| Elevation | Copernicus GLO-30 DSM (AWS COG `N25E063`) | 30 m (1 arc-sec) | Chosen over SRTM (older, voids) and ALOS AW3D30 (not reachable). It is a **surface** model: post reads 143 m vs RL 133 surveyed (+10 m, structures/DSM bias). Vertical abs. accuracy ≈ ±4 m (LE90); badland gullies < 30 m wide are **not resolved**. |
| Imagery | Esri World Imagery z16/z17/z18 | ~0.6 m at z18 | Capture date unknown (Esri composite). Used for track/footpath search, bedding traces and texture. |
| Route | user KMZ | — | Existing tr Ch 0–3.92, new tr Ch 3.92–5.23, kacha tr Ch 5.23–5.92 |
| Drone | WhatsApp clip, 848×480 | — | No telemetry: locations are **assessed** from ridge-shape matching |

Local coordinates: equirectangular metres about 25.415 N, 63.435 E (scale error < 0.1 % over the AOI; equivalent to UTM 41N for these distances).

## Analysis
- **Slope / aspect:** central differences on a 10 m bicubic resample of GLO-30.
- **Drainage:** priority-flood depression fill → D8 accumulation; nala = catchment > 5 ha (crossings) / > 2 ha (map).
- **Track discovery:**
  - Imagery: no vehicle track to the hill post is visible. A faint light line runs W from the post along the ridge spine, assessed as a footpath (**unconfirmed**).
  - LCP: Dijkstra on the 10 m grid, 48-neighbour edges up to 30 m. Edges steeper than the ruling limit (1:7, or 1:5 for the "direct" case) are removed. Cost = length × (1 + 3·excess grade over 1:10 / 0.04) × (1 + 0.6·side slope over 12°/10°) + 0.5 × length in nalas over 5 ha.
  - Sources: anywhere on the KMZ tracks. Target: the post.
  - Each approach sector (S, W, N, E) is forced in turn by blocking the other sectors within 40–300 m of the post. This tests the "rear / N foothill" hypothesis without assuming it.
- **Per-track metrics:** paths smoothed (σ 10 m), resampled every 5 m and draped on the DEM.
  - Grade is measured over a 50 m window. "% over 1:10 / 1:7 / 1:5" is the share of length.
  - A hairpin is a heading change over 110° within 80 m.
  - Cut is side-hill bench cut for a 4.3 m (14 ft) formation, plus grade-cutting to a 1:7 cut-only envelope. This is a **coarse 30 m DEM estimate (±50 %, assessed)**, for ranking only, not for BOQ.
  - Fill = 0.45 × bench cut.
- **Exposure:** line of sight from observers (+2 m) to each track point (+3 m, vehicle). Two observer sets, both **assumed** and to be confirmed by you:
  - (a) dominating ground: 12 crest points of the Taloband range above 160 m, within 4 km;
  - (b) W/NW low ground: Turbat Rd and the Shadi Kaur plain, 11 points.
- **MCDA:**
  - Min–max scores, 1 = best. Weights: gradient 20, exposure 20, construction effort 15, length 10, drainage 10, stability 10, trafficability 10, maintenance 5.
  - Weights were set before scoring and not tuned.
  - Sensitivity: each weight ±20 % (16 runs), plus exposure ×2 and ×0.5, gradient ×0.5, length ×2, plus a "KMZ new tr built anyway" case.
- **Geology (assessed):**
  - Cross-sections through the post show a steep S face (≈21° mean over 250 m) and a gentle N side falling into a strike hollow (≈85 m).
  - Imagery bedding traces strike ENE–WSW, and the drone clip at 1:03 shows bedding outcropping on the S face.
  - Interpretation: beds dip **N**, so the S face is the scarp (dip into slope) and the N side is the dip slope (dip out of slope).
  - **Unconfirmed:** this needs a ground dip reading, or the camera heading of the annotated oblique.

## What is NOT claimed
- The T1–T5 alignments are LCP-derived lines on a 30 m DEM, not surveyed alignments. Final pegging needs ground recce.
- No figure on screen will be typed by hand. All are read from `work/metrics.json` / `mcda.json`, produced by the scripts.
