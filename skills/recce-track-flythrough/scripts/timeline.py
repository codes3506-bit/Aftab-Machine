# Shared timeline: global time t (s) -> scene time / chainage / shot.  30 fps.
import numpy as np, json
FPS = 30
R = '/home/user/recce'
import os
VID = int(os.environ.get('VID', '1'))
SC = json.load(open(f'{R}/work/' + ('scene.json' if VID == 1 else 'scene2.json')))
CREST = SC['crest_ch']
LEN = float(SC['track']['ch'][-1]) if VID == 2 else 9.0

# (t_start, t_end, ch_start, ch_end) for the fly-through; pauses hold chainage
FLY1 = [(45.0, 59.0, 0.00, 3.00),
       (59.0, 63.0, 3.00, 3.40),
       (74.0, 81.0, 3.40, CREST),
       (93.0, 102.0, CREST, 5.30),
       (102.0, 115.0, 5.30, 9.00)]
PAUSES1 = [  # (t0, t1, id) background frozen
    (32.0, 45.0, 'brief'),
    (63.0, 74.0, 'ascent'),
    (81.0, 93.0, 'crest')]
SHOTS1 = [(0, 9, 'title'), (9, 25, 'area'), (25, 32, 'descend'), (32, 45, 'brief'),
          (45, 115, 'fly'), (115, 128, 'grade'), (128, 152, 'finale')]
# video 2 – Opt 2 (west altn tr)
FLY2 = [(46.0, 59.0, 0.00, CREST), (70.0, 76.0, CREST, 3.13), (86.0, 102.0, 3.13, LEN)]
PAUSES2 = [(32.0, 46.0, 'brief'), (59.0, 70.0, 'saddle'), (76.0, 86.0, 'nullah')]
SHOTS2 = [(0, 9, 'title'), (9, 25, 'area'), (25, 32, 'descend'), (32, 46, 'brief'),
          (46, 102, 'fly'), (102, 115, 'grade'), (115, 145, 'finale')]
FLY, PAUSES, SHOTS = (FLY1, PAUSES1, SHOTS1) if VID == 1 else (FLY2, PAUSES2, SHOTS2)
DUR = 152.0 if VID == 1 else 145.0
T_FLY0, T_FLY1 = SHOTS[4][0], SHOTS[4][1]
T_GRADE1 = SHOTS[5][1]


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def chain_at(t):
    if t < FLY[0][0]:
        return 0.0
    for a, b, c0, c1 in FLY:
        if t < a:
            return c0
        if t <= b:
            u = (t - a) / (b - a)
            # ease only at segment ends that touch a pause
            return c0 + (c1 - c0) * u
    return LEN


# gaussian-smoothed chainage for velocity continuity (except holds stay exact)
_T = np.arange(0, DUR, 1 / FPS)
_C = np.array([chain_at(t) for t in _T])


def _smooth_ch():
    from scipy.ndimage import gaussian_filter1d
    c = gaussian_filter1d(_C, 9)
    for a, b, _ in PAUSES[1:]:
        m = (_T >= a - 0.05) & (_T <= b + 0.05)
        c[m] = _C[m]
    # blend into holds smoothly over 0.6 s
    for a, b, _ in PAUSES[1:]:
        for edge, sgn in ((a, -1), (b, 1)):
            m = (_T > edge - 0.7) & (_T < edge + 0.7) & ~((_T >= a) & (_T <= b))
            w = smooth(np.abs(_T[m] - edge) / 0.7)
            c[m] = _C[m] * (1 - w) + c[m] * w
    c[_T < FLY[0][0]] = 0
    return np.maximum.accumulate(c)


CHS = _smooth_ch()


def ch(t):
    i = int(min(len(CHS) - 1, max(0, round(t * FPS))))
    return float(CHS[i])


def frozen(t):
    """scene time actually rendered (constant inside pauses)"""
    for a, b, _ in PAUSES:
        if a <= t < b:
            return a
    return t


def pause_at(t):
    for a, b, k in PAUSES:
        if a <= t < b:
            return k, t - a, b - a
    return None
