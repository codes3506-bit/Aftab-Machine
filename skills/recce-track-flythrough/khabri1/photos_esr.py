"""Gr recce photos -> Real-ESRGAN x4 (tiled, ONNX CPU) -> 2x size JPEG q95 in /home/user/khabri/photos_esr."""
import sys, os, numpy as np, onnxruntime as ort, cv2
src = sys.argv[1]; out = '/home/user/khabri/photos_esr'; os.makedirs(out, exist_ok=True)
S = ort.InferenceSession('/home/user/khabri/models/esr.onnx')
for n in range(1, 11):
    im = cv2.cvtColor(cv2.imread(f'{src}/{n}.jpg'), cv2.COLOR_BGR2RGB).astype(np.float32) / 255; h, w = im.shape[:2]; T = 400; P = 16
    o = np.zeros((h * 4, w * 4, 3), np.float32)
    for y in range(0, h, T):
        for x in range(0, w, T):
            y0, x0 = max(0, y - P), max(0, x - P); y1, x1 = min(h, y + T + P), min(w, x + T + P)
            r = S.run(None, {'input': im[y0:y1, x0:x1].transpose(2, 0, 1)[None]})[0][0].transpose(1, 2, 0)
            oy, ox = (y - y0) * 4, (x - x0) * 4; hh, ww = min(T, h - y) * 4, min(T, w - x) * 4
            o[y * 4:y * 4 + hh, x * 4:x * 4 + ww] = r[oy:oy + hh, ox:ox + ww]
    o = cv2.resize(np.clip(o, 0, 1), (w * 2, h * 2), interpolation=cv2.INTER_AREA)
    cv2.imwrite(f'{out}/{n}.jpg', cv2.cvtColor((o * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95]); print('photo', n, flush=True)
