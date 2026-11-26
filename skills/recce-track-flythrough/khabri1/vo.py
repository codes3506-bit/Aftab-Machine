"""Voice-over for the Khabri-1 options film (v4). Every figure is read from work/*.json and spoken in words.
Neural TTS (Kokoro-82M, ONNX, local): blend of British male voices, pitched slightly down, broadcast chain
(HPF, warmth, presence, compression). Writes work/vo/<id>.wav (48 kHz mono) and work/vo/vo.json {id: [text, seconds]}."""
import json, os, subprocess, sys, numpy as np, soundfile as sf
from geo import *
from kokoro_onnx import Kokoro

MT = {t['name']: t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}; POL = json.load(open(f'{R}/work/pol.json')); PAD = json.load(open(f'{R}/work/pad.json'))
FX = json.load(open(f'{R}/work/film_facts.json'))          # written by final3.py --facts (face slopes, KMZ km)
ORD = ['T1', 'T2', 'T3', 'T4', 'T5']

U1 = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()
def w(n):
    n = int(round(n))
    if n < 20: return U1[n]
    if n < 100: return TENS[n // 10] + ('' if n % 10 == 0 else '-' + U1[n % 10])
    if n < 1000: return U1[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' and ' + w(n % 100))
    if n < 1000000: return w(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else (' and ' if n % 1000 < 100 else ' ') + w(n % 1000))
    return str(n)
def dec(x, nd=1):
    s = f'{x:.{nd}f}'; a, b = s.split('.'); return w(int(a)) + ' point ' + ' '.join(U1[int(c)] for c in b)
def rnd(x, base): return int(round(x / base) * base)

NAME = {'T1': 'Option one. A direct climb, straight up the south spur.', 'T2': 'Option two. A graded line, zig-zagging up the south spur.',
        'T3': 'Option three. The west spur, climbing along the ridge.', 'T4': 'Option four. The east flank, arriving along the crest neck.',
        'T5': 'Option five. Around the rear, along the northern foothill, climbing from the north.'}
def opt(k):
    m = MT[k]; p = POL[k]; s = [NAME[k], (f"{w(rnd(m['new_const_m'], 10))} metres of new construction." if m['new_const_m'] < 1000 else f"{dec(m['new_const_m'] / 1000, 2)} kilometres of new construction."), f"Maximum grade, {w(m['max_grade_pct'])} percent"]
    if m['pct_gt_1in5'] >= 1: s[-1] += f"; {w(m['pct_gt_1in5'])} percent of its length is steeper than one in five."
    else: s[-1] += f"; {w(m['pct_gt_1in7'])} percent steeper than one in seven."
    hp = m['hairpins']; nx = m['nala_xings']
    s.append(('No hairpins' if hp == 0 else f"{w(hp)} hairpins") + ('' if nx == 0 else f", and {w(nx)} nala crossings") + '.')
    s.append(f"About {w(rnd(p['cut_total'], 100))} cubic metres of cut, {w(rnd(p['total'], 100))} litres of P O L, and {w(p['dur'])} work days.")
    return ' '.join(s)

cuts = [POL[k]['cut_total'] for k in ORD]; pols = [POL[k]['total'] for k in ORD]; nk = [MT[k]['new_const_m'] / 1000 for k in ORD]
LINES = {
 'open': "Khabri One hill post, on the Taloband Range. This brief sets out five alignments for a track to the post, as options for decision.",
 'orient': f"The post stands on the crest of the range, at a reduced level of one hundred and thirty-three metres. The K M Z track, {dec(FX['kmz_km'], 1)} kilometres, runs along the foot of the range. Every alignment takes off from it.",
 'air': "From the air, this is badlands country. Eroded shale spurs, deep gullies, and bedding exposed on every face.",
 'slope': f"The faces below the post average {w(FX['face_s'])} degrees on the south, and {w(FX['face_n'])} on the north. Drainage lines cut across every approach.",
 'section': "In section, the post sits on a narrow crest. The beds appear near-horizontal, and no dip-slope face has been identified. This is to be confirmed on the ground.",
 'climb': "On the ground, the approach climbs over loose shale scree and slabs, between steep, gullied spurs of white silt-shale. The post stays on the skyline throughout the climb.",
 'align': "Five alignments were traced as least-cost corridors on the terrain model. Each takes a distinct line to the crest.",
 'postair': "The post from the air. On the crest line, with steep, gullied faces falling away below it.",
 **{k: opt(k) for k in ORD},
 'top1': f"At the top, the crest is a narrow ridge of platy shale, running east-north-east. An existing room, {w(PAD['room_ft'])} by {w(PAD['room_ft'])} feet, stands on it. A pad of {w(PAD['pad_ft'])} by {w(PAD['pad_ft'])} feet is required alongside, for the post.",
 'top2': (f"Sited on the crest alongside the room, the pad needs a level formation about {dec(PAD['formation_below_high'], 1).replace('zero point', 'point')} of a metre below the high point. "
          f"Some {w(rnd(PAD['cut'], 5))} cubic metres of cut, balanced by fill. "
          f"{w(PAD['rows'][0]['q']).capitalize()} excavator {'hour' if PAD['rows'][0]['q'] == 1 else 'hours'} and {w(PAD['rows'][1]['q'])} dozer {'hour' if PAD['rows'][1]['q'] == 1 else 'hours'}; about {w(PAD['total'])} litres of P O L, and {w(PAD['days'])} working day. "
          f"The terrain model smooths a narrow crest, so this is to be confirmed by levels on the ground."),
 'compare': (f"Side by side. New construction runs from {dec(min(nk), 1)} to {dec(max(nk), 1)} kilometres. "
             f"Cut, from about {w(rnd(min(cuts), 100))} to {w(rnd(max(cuts), 1000))} cubic metres. And P O L, from about {w(rnd(min(pols), 100))} to {w(rnd(max(pols), 1000))} litres."),
 'close': "All figures are assessed from a thirty-metre terrain model, and are to be confirmed by ground recce before pegging. The five options are presented in no order of preference. For decision.",
}

if __name__ == '__main__':
    out = f'{R}/work/vo'; os.makedirs(out, exist_ok=True)
    k = Kokoro('/home/user/khabri/models/kokoro.onnx', '/home/user/khabri/models/voices.bin')
    style = 0.7 * k.get_voice_style('bm_lewis') + 0.3 * k.get_voice_style('bm_george')
    only = sys.argv[1:] or list(LINES)
    meta = json.load(open(f'{out}/vo.json')) if os.path.exists(f'{out}/vo.json') else {}
    for key in only:
        txt = LINES[key]; a, sr = k.create(txt, voice=style, speed=0.95, lang='en-gb'); raw = f'{out}/{key}_raw.wav'; sf.write(raw, a, sr)
        chain = ('rubberband=pitch=0.955:formant=preserved,highpass=f=65,equalizer=f=140:t=q:w=1.0:g=2.5,equalizer=f=320:t=q:w=1.2:g=-1.5,'
                 'equalizer=f=3200:t=q:w=1.2:g=2.0,equalizer=f=7000:t=q:w=2:g=-1.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3dB,aresample=48000')
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', chain, '-ac', '1', f'{out}/{key}.wav'], check=True); os.remove(raw)
        d = sf.info(f'{out}/{key}.wav').duration; meta[key] = [txt, round(d, 2)]; print(f'{key:8s} {d:5.1f}s  {txt[:90]}', flush=True)
    json.dump(meta, open(f'{out}/vo.json', 'w'), indent=1)
