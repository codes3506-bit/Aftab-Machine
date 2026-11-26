"""Drone clean-up: light temporal denoise -> Real-ESRGAN general x4v3 (ONNX, CPU) -> 2x master, crop clear of player bar.
Source is a 848x480 screen recording; rows 0-400 hold picture (player bar below). Output 3392x1600 @ 30 fps, crf 12."""
import subprocess, sys, numpy as np, onnxruntime as ort, time
SRC = sys.argv[1]; OUT = sys.argv[2]; SS, DU = sys.argv[4], sys.argv[5]; W0, H0 = 848, 480; CH = 400
so = ort.SessionOptions(); so.intra_op_num_threads = int(sys.argv[3]) if len(sys.argv) > 3 else 4
S = ort.InferenceSession('/home/user/khabri/models/esr.onnx', so)
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', SS, '-t', DU, '-i', SRC, '-vf', 'hqdn3d=1.5:1.5:4:4', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W0*4}x{CH*4}', '-r', '30', '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv444p', OUT], stdin=subprocess.PIPE)
f = 0; t0 = time.time()
while True:
    raw = dec.stdout.read(W0 * H0 * 3)
    if len(raw) < W0 * H0 * 3: break
    x = np.frombuffer(raw, np.uint8).reshape(H0, W0, 3)[:CH].astype(np.float32) / 255
    y = S.run(None, {'input': x.transpose(2, 0, 1)[None]})[0][0].transpose(1, 2, 0)
    enc.stdin.write((np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); f += 1
    if f % 60 == 0: print(f'esr {f} {time.time()-t0:.0f}s', flush=True)
enc.stdin.close(); enc.wait(); print('done esr', f, flush=True)
