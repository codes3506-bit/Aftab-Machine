# Methods, data and accuracy limits

## Data
| Layer | Source | Resolution | Note |
|---|---|---|---|
| Elevation | Copernicus GLO-30 DSM (AWS COG `N25E063`) | 30 m (1 arc-sec) | Chosen over SRTM (older, voids) and ALOS AW3D30 (not reachable). It is a **surface** model: post reads 143 m vs RL 133 surveyed (+10 m, structures/DSM bias). Vertical abs. accuracy ≈ ±4 m (LE90); badland gullies < 30 m wide are **not resolved**. |
| Imagery | Esri World Imagery z16/z17/z18 (analysis); **Esri World Imagery Wayback release 32553, 15 Aug 2024** (film v3 texture) | ~0.6 m at z18 | The current Esri release over Khabri is a soft, hazy capture. Of the 4 distinct captures in the Wayback archive (2022-08, 2023-08, 2024-08, 2026-05), the 2024-08-15 release is the sharpest recent one and is used to texture the film terrain. Track analysis is unchanged. |
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
  - Cut is side-hill bench cut for a 4.3 m (14 ft) formation, plus grade-cutting to a 1:7 cut-only envelope. This is a **coarse 30 m DEM estimate (±50 %, assessed)**, for comparing options only, not for BOQ. The film and table show cut on the same basis as POL: the new alignment plus the KMZ new tr portion it uses.
  - Fill = 0.45 × bench cut.
- **Exposure:** line of sight from observers (+2 m) to each track point (+3 m, vehicle). Two observer sets, both **assumed** and to be confirmed by you:
  - (a) dominating ground: 12 crest points of the Taloband range above 160 m, within 4 km;
  - (b) W/NW low ground: Turbat Rd and the Shadi Kaur plain, 11 points.
- **MCDA (desk analysis only, not shown in the film):** the client asked for options without a recommendation, so no score, weight or rank appears on screen.
  - Min–max scores, 1 = best. Weights: gradient 20, exposure 20, construction effort 15, length 10, drainage 10, stability 10, trafficability 10, maintenance 5.
  - Weights were set before scoring and not tuned.
  - Sensitivity: each weight ±20 % (16 runs), plus exposure ×2 and ×0.5, gradient ×0.5, length ×2, plus a "KMZ new tr built anyway" case.
- **Geology (assessed, revised after the recce oblique):**
  - Mean slope within 30–250 m of the post (Cop GLO-30, 10 m sampling): S face ≈ 22°, N face ≈ 23° (direct bicubic DEM sampling; an earlier 24° came from the render mesh). The N face drops about 60 m to a strike hollow about 205 m N (DSM ≈ 84 m). An earlier note of a gentle (≈ 8°) N side was wrong and has been withdrawn.
  - Bedding strikes ENE–WSW on imagery.
  - Bedding crops out on **both** faces: the S face in drone clip 01:03, and the N side in the user's annotated oblique. The oblique is assessed as looking S from the N side, since it shows badlands beyond the crest and no river plain.
  - Read: beds gently dipping or near-horizontal. No dip-slope (planar-slide) face is identified. An earlier "beds dip N" reading, based on ridge asymmetry alone, was withdrawn.
  - **Unconfirmed:** take a dip reading on the ground.
- **POL / work days:** the `pol-work-days-calculator` engine with the user's saved standards (`userstd.json`) and a 10 % hidden margin.
  - Sections typed per 5 m: nala where catchment > 5 ha; cut & fill where cross slope > 15 %; levelling elsewhere.
  - Cut is excavated at the hill-cutting standard (34 m³/hr), and spoil is dozed at 95 m³/hr.
  - Vehicle moves are assumed: FBT 2 × 20 km, SC 10 × 40 km round trip, civ trk 2 × 20 km.

## What is NOT claimed
- The T1–T5 alignments are LCP-derived lines on a 30 m DEM, not surveyed alignments. Final pegging needs ground recce.
- No figure on screen is typed by hand. All are read from `work/metrics.json` / `pol.json`, or computed from the DEM at render time. The only literal inputs are the post RL (133 m) and coordinates, given by the user.
- Elevations shown in the film are from Cop GLO-30, a surface model. It reads about 10 m above the given RL at the post (143 m vs 133 m).

## Film v3 (B3-Haryaan look)
- 3D terrain: Cop GLO-30 at **vertical exaggeration ×1.5** (as in the B3 film), relief shading, sun 135°/42°. Rendered natively at 2560×1440. The camera is set back so that one imagery pixel is about one screen pixel; closer cameras only magnify the 0.6 m imagery and look soft.
- Imagery checked and rejected: current Esri release (soft), Esri z19 (no data here), Mapbox satellite (same soft Maxar capture). Bing tiles were not used.
- Elevations shown on screen (HUD, profiles, section) are true metres, not exaggerated.
- Gr recce photos (5, no GPS) are shown at a stop on each option. They are captioned "not geotagged – representative of the ground on the approaches". Each is matched to the option only by terrain type (for example, the nala-bed photo with T5, which has the nala crossings). They are not claimed to be on the alignment.
- Drone footage (no telemetry) is used at 5 points: 00:00–00:09, 00:26–00:34, 00:58–01:08 (strata), 01:02–01:08 (post), all labelled "view assessed".
