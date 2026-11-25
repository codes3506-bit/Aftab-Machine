# 00 · Capabilities, gaps and workarounds

Cloud container: Linux, 4 vCPU, 15 GB RAM, no GPU (Mesa llvmpipe OpenGL under `xvfb-run`). No user computer is attached.

## Inputs
| Brief path | What was actually supplied | Status |
|---|---|---|
| `inputs/route.kmz` | `Khabri1_Opt1_Track_rev.kmz` (CHW → existing tr → new tr → kacha tr → plain pad RL ~25) | ✅ parsed. **Target agreed with user: hill post RL 133** (25°25'38.6"N 63°26'23.2"E, from previous brief) |
| `inputs/drone/*.mp4` + SRT | `WhatsApp_Video_2026-11-25_at_10.26.14.mp4`: 848×480, 70.7 s, already annotated, **no SRT / GPS / flight log** | ⚠ used as supplied (user's choice). Geotags are *assessed* by matching ridges to the DEM. No photogrammetry DSM is possible at 480p without poses. |
| ground photos | 5 recce photos (soldiers in wadi, post on hilltop) + 1 annotated oblique of the post (perimeter, "Fclb"/"Matur" marks) | ⚠ the annotated oblique arrived as a chat image, not a file. **Needs to be re-sent as a file** to appear in the film. |
| `inputs/reference/prev_version.mp4` | `Khabri1_Track_3D_Final_1080p.mp4` (84 s) | ✅ used as style reference only |

## Skills
| Skill | Status | Use |
|---|---|---|
| repo skill `recce-track-flythrough` | ✅ loaded | pipeline basis (Esri + GLO-30, moderngl, HUD, POL engine) |
| `video-shotcraft` | ✅ loaded | shot rules applied: one motion per shot, ≥1 s holds, riser→impact into the reveal, independent final review. Its Remotion product-promo templates do not fit terrain. |
| `anthropic-skills:video-making` | ❌ not in this account's skill list | replaced by the repo skill + video-shotcraft |
| `geoai:*` (orchestrator, GEE, terrain-hydrology, MCDA, network/LCP, cartography…) | available, **not loaded** | the methods were implemented directly in Python (D8 + priority-flood, Dijkstra LCP, MCDA + sensitivity, LOS viewshed). Earth Engine is not reachable/authenticated here (see below). |
| `videodb:videodb` | ❌ MCP failed (proxy 403) | clip logged manually at 1 fps with timecodes (see storyboard / evidence) |
| `social-media-skills:veo-3 / kling / runway / luma` | available | **not used**: the brief bans generative video for ground; no atmospheric transition needs it yet |
| `ai-voiceover`, `ai-music-and-sound` | available | to be used after the checkpoint (VO optional; original score generated procedurally as in the previous film) |
| `engr-handbook-tfc-qty-conversions`, `pol-work-days-calculator`, `military-report-expression`, `service-abbreviations`, `military-terms-glossary` | available | to be loaded for the POL / work-days annex and the recce report **after the track is confirmed** |

## Connectors
| Connector | Status | Note |
|---|---|---|
| Google Earth via your Chrome | ❌ no computer attached to this session | Google tiles / Photorealistic 3D Tiles need an API key and the host is blocked. Used **Esri World Imagery 0.5 m** (host allowed for this env on your approval) + **Copernicus GLO-30**. To use Google 3D Tiles, provide a Maps API key and I'll add `tile.googleapis.com`. |
| Earth Engine | ❌ not authenticated | GLO-30 read directly from the AWS COG (same data GEE serves) |
| Mapbox / Felt / TomTom | available | not needed: geometry and lengths computed locally in UTM-equivalent local metres |
| Adobe / Canva / HyperFrames / Higgsfield | available | final render is local ffmpeg (H.264 High + ProRes 422 HQ master); HyperFrames compose is disabled for CLI clients |
| Sentinel-2 COGs (AWS) | reachable | reserve option for a dated scene / change detection |

## Tooling built
`skills/recce-track-flythrough/khabri1/`: `fetch.py` (imagery) · `geo.py` · `route.py` (sector-forced LCP) · `metrics.py` (grades, cut, nala xings, exposure) · `mcda.py` · `export.py` (GeoJSON/KMZ/maps) · `engine.py` (GPU terrain) · `overlay.py` (glow tracks, HUD) · `styleframes.py` · `evidence.py`
