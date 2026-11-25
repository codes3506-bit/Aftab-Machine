# Storyboard · Khabri-1 Hill Post: Track Recce (2:00)

3840×2160 · 30 fps · 3,600 frames · also 1080p. Grade: one look for 3D and drone (lifted blacks, warm highlights, soft vignette).
Type: Inter / Inter Display, JetBrains Mono for live figures. Gold `#F5B700` = recommended / focus; muted hues for the other tracks.
Camera: all moves on Catmull-Rom splines with eased (cubic-bezier 0.45,0,0.2,1) time remap. No linear moves; heading rate ≤ 12°/s.
Shot rules: one motion idea per shot; ≥ 1 s hold after each key figure lands; 3 s for the opening action.

| # | TC | Dur | Picture | Camera | Overlays / on-screen text | Audio |
|---|---|---|---|---|---|---|
| 1 | 0:00–0:10 | 10 s | **Drone** 0:37→0:47 (range S face, golden light), graded, 1.08× slow push-in (digital, stabilised) | slow push-in | Title fades in at 0:04: **TRACK RECCE · KHABRI-1 HILL POST**; sub: *Selecting the alignment to the post*. Geotag chip: `DRONE 00:37 · TALOBAND RG S FACE · ASSESSED` | wind bed, low pad enters |
| 2 | 0:10–0:25 | 15 s | **3D orbit** over real terrain. Match-cut from drone 0:47 into the 3D at the same heading. | 70° orbit about the post at 2.4 km, alt 1,050 m, descending to 800 m | Post pin drops in at 0:13 (RL 133, grid). AOI outline draws on 0:15–0:18. KMZ track (grey) draws CHW → take-off 0:18–0:23. North arrow throughout. | pin "tick", pad swells |
| 3 | 0:25–0:37 | 12 s | **Slope tint** washes over a 2 km corridor. Drainage lines then "flow" downhill (animated along D8 order). | slow lateral truck from SE, alt 520 m | Slope legend (deg). Callout: **S face ≈ 21° · N side ≈ 8° into a strike hollow**. Nala catchments > 5 ha labelled. | soft data-shimmer |
| 4 | 0:37–0:50 | 13 s | **Strata:** split screen. Left: 3D N–S cross-section slicing through the post (DEM wall). Right: drone 1:03 (S face bedding). | locked-off section, gentle 3D rotate | Bedding strike ENE–WSW. **Assessed dip N: S face = scarp (beds into slope), N side = dip slope (beds out of slope)**. Tag: `ASSESSED · confirm on ground` + drone TC 01:03. User oblique (if re-sent) as a 3rd inset. | low hit on the section cut |
| 5 | 0:50–1:15 | 25 s | **Tracks draw on** one by one, each with a travelling-light pulse, and remain together: T1 (0:50) → T2 (0:54) → T3 (0:58) → T4 (1:02) → T5 (1:06), hold all 1:10–1:15 | slow 40° orbit at 1.6 km | Per-track chip + mini elevation profile (3 s each): length · max grade · % > 1:10. Legend panel left. | 5 soft "draw" swells, building |
| 6 | 1:15–1:35 | 20 s | **Reveal T5 (rear / N foothill):** others dim to 55 %. T5 goes gold with the strongest glow. | low chase-cam (70–90 m above track, 170–330 m behind) on a smoothed spline: W foot → N along foothill → climbs through the N hollow to the post. Ends in a rising crane over the post. | Live HUD: CH · ELEV · GRADE (from profile). Profile strip with playhead. Call-outs: "leaves KMZ tr Ch 4.68", "N foothill", "climbs in the strike hollow, defilade from S", "6 nala xings". | riser 1:12 → impact at 1:15 (only full-frame hit) → sustained pad |
| 7 | 1:35–1:52 | 17 s | **Comparison:** split. Left: plan view (N-up, scale bar) with exposure: red = seen from dominating crests, orange = seen from W/NW low ground. Right: radar + table. | top-down, slow 5 % zoom | Table T1–T5: new const · max/mean grade · % > 1:10/1:7/1:5 · hairpins · nala xings · cut (assessed) · exposure · MCDA. Sensitivity strip: "± 20 % on every weight → T4 first in 16 / 16". | ticks on each row |
| 8 | 1:52–2:00 | 8 s | **Recommendation card** over a blurred final frame | static, 1.5 s fade to black | `RECOM: T-x (…)` + key figures: new const, max grade, % > 1:10, cut, nala xings, POL / work days (from POL engine), **pending the checkpoint decision** (see below) | resolve chord, wind out |

Inserts: drone frames always carry `DRONE mm:ss · place · ASSESSED`. Plan views always carry a north arrow and a 500 m scale bar.

## Decisions taken after the checkpoint
- User: go ahead. Beat 8 = **RECOM T5, ALTN T4, gr recce both** (stated tie-breakers: grade for loaded vehicles, crest exposure). The card shows the MCDA order (T4 0.79 v T5 0.76) openly.
- Beat 4 geology revised after the user's annotated oblique: bedding on both faces, so beds gently dipping (assessed).

## Decision context (as presented at the checkpoint)
The data does **not** cleanly confirm the expected outcome:
- **T4 (E flank)** scores **0.79** and **T5 (rear / N foothill)** scores **0.76**. If the KMZ new tr is built anyway: **0.765 vs 0.763**, effectively a tie.
- **T5 wins on gradient and stability of work:** max 16.6 %, mean 7.6 %, only 33 % over 1:10, 0 % over 1:5, least cut (≈ 2.6k m³ assessed), lowest exposure to the dominating crests (34 %).
- **T5 loses on length and drainage:** 2.41 km new const including 0.76 km of the KMZ new tr, 6 nala xings, and 74 % visible from W/NW low ground.
- **T4** is short (1.08 km) with no nala xings, but steeper (55 % over 1:10, 8 hairpins) and more exposed to the crests (50 %).

Options for beat 8: (a) recommend T5 with the trade-offs stated; (b) recommend T4; (c) "T4 / T5 equal on desk study: ground recce both". Beats 6–7 also change if you confirm which observation threat matters (crests vs W/NW low ground).
