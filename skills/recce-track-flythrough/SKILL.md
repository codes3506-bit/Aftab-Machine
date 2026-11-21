---
name: recce-track-flythrough
description: Turn a track recce (KMZ alignment with work-type sections, chainage, nullah xings, hy const areas; reference slides; ground recce photos; Div POL Calculator HTML) into a professional 3D flythrough MP4 that explains to a commander how difficult the track is to construct. Real satellite imagery (Esri z16-z18, 0.54 m/px at the track) on real Copernicus GLO-30 terrain, live chainage/elev/grade HUD, paused info panels with photos and elevation profile, slope analysis, and a slide-vs-recce POL / days / machinery assessment computed with the user's own POL Calculator engine. Use when the user asks for a recce / track / route difficulty video or flythrough from a KMZ.
---

# Recce track flythrough (difficulty brief)

First built for **"Recce Altn Tr Const - B3 to Haryaan BOO"** (23 EB / 44 Div, Nov 2026).
Output: 1920x1080, 30 fps, H.264 + AAC, ~152 s. Sister skill: `track-3d-flythrough` (Khabri-1, built from slides only).

## Inputs the user gives
- **KMZ** (source of truth): main LineString, per-section placemarks named `Levelling / Cut & fill / Nullah filling – Ch a–b km`,
  chainage points, nullah xing points, hy const area polygons. Ser folders may hold several tracks – pick the right `Ser`.
- **Slides**: scope-of-work slide (reference figures: Opt 1 POL / hrs / days) and area-orientation slide (place labels).
- **Ground recce photos** (pasted in chat → recover from the session `.jsonl`, base64 `image` blocks; no GPS – ask or place on the
  matching stretch and say so).
- **POL Calculator HTML** – run its own `calc()` engine in node (`scripts/polrun.js`), using the **user's saved standards** read
  from the saved page's `data-s` inputs (`userstd.json`), not the built-in DEF values. Days = `Math.ceil(dur)` like the UI.
- **Logos / font**: ask for logo PNGs and the font file (Candara is a Windows font – `C:\Windows\Fonts\Candara*.ttf`).
  Drop them in `assets/` as `logo_23eb.png`, `logo_44div.png`, `Candara.ttf`, `Candarab.ttf`, `Candarai.ttf`, `Candaraz.ttf`;
  `hud.py` falls back to Carlito + placeholder roundels.

## Network / tools
Google Earth / Google tiles are **not reachable** from the cloud container (and need a key) – use Esri World Imagery
(`server.arcgisonline.com`) + Copernicus GLO-30 COG (`copernicus-dem-30m.s3.amazonaws.com`). Both were reachable by default.
Python venv: `moderngl numpy scipy pillow opencv-python-headless tifffile imagecodecs matplotlib`; render under
`xvfb-run -a -s "-screen 0 1920x1080x24"` (llvmpipe GL 4.5, ~1.6 s/frame at 1080p with 4x MSAA on 4 vCPU).

## Sequence
1. Unzip KMZ, extract the Ser section → `sera.json` (track, sections, chainage, nullahs, hy polygons, posts).
2. `fetch.py` – imagery z16 (wide area), z17, z18 (around track) + DEM COG.
3. `reg2.py` – SIFT + `estimateAffinePartial2D` to georeference the area-orientation slide on z16 (slides may be rotated;
   check a known post lands within ~50 m). Gives coordinates for place labels.
4. `dem.py` / `analyse.py` – sample DEM along the track every 5 m; grade over 50/100/200 m windows (quote 100 m for "max grade",
   50 m for "pitches"); cross slope; rock volume = side-hill bench + grade-cutting to 1:7 (cut-only envelope). Chainage scaled to
   LU recce length. Validate DEM vs slide elevation profile.
5. `polrun.js proj.json out.json` – POL & days through the user's engine (rock as Excavation rows @ hill-cutting std,
   dozing of spoil as Other plant @ dozer spreading rate). Run 1 dozer+1 exc and a larger fleet variant.
6. `prep.py` (textures + 6 m heightmap over full z16 extent), `scene.py` (track samples, labels).
7. `render.py OUT.mp4 [--stills t,..] [--scale .5]` – terrain + ribbons only; writes `OUT_cams.json` (label screen coords +
   occlusion). Always check stills first. Pauses reuse the frozen frame (no re-render).
8. `hud.py terrain.mp4 hud.mp4` – titles, logos, labels, live HUD, pause panels, photos, tables. Re-run alone to change
   font / logos / wording (≈10 min) – no terrain re-render needed.
9. `audio.py` – pad + wind + SFX (video-shotcraft library) → `soundtrack.wav`; mux with ffmpeg, two-pass to ~25-30 MB.

## Storyboard (timeline.py)
0-9 title card (logos either side) · 9-25 area orientation orbit (slide-2 labels, preview dashed track, hy const areas) ·
25-32 descend to B-3 · 32-45 **pause**: scope of work + terrain stats + elevation profile over blurred frozen frame ·
45-115 chase fly-through (live CH / ELEV / GRADE / work type + profile strip; km, N xing, crest labels) with **pauses** at the
ascent (Ch 3.4) and crest (Ch 4.05) showing recce photos + facts · 115-128 grade overview (track coloured by grade, slope tint
in a 1 km corridor, KMZ slope legend) · 128-152 slide-vs-recce table, POL calculator table + machinery, assessment, fade.

## Lessons
- Don't trust a single SIFT homography with few inliers; similarity fit across several scales gave 224 inliers.
- KMZ end point name and slide place names can differ ("Haryan VP" vs "Haryan BOO" vs slide "Haryan") – label from the KMZ,
  mention the difference.
- Esri imagery is olive-tinted; a blue haze makes it green – warm WB (`*vec3(1,0.99,1.13)`) and neutral haze.
- Ribbon outline + fill at the same depth z-fight → lift the fill slightly more and don't write depth for the outline.
- Slope tint over a whole mountain range is just purple – restrict to a corridor mask around the track.
- PIL: build panels opaque, then scale alpha; drawing translucent fills directly replaces alpha.
