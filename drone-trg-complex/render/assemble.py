"""Join the rendered shots with 0.7 s crossfades, fade to black at the end, add the soundtrack."""
import glob, json, os, subprocess
V = os.path.join(os.path.dirname(__file__), '..', 'build', 'video')
OUTF = os.path.join(os.path.dirname(__file__), '..', 'deliverables', 'Drone_Trg_Complex_44_Div.mp4')
files = sorted(glob.glob(os.path.join(V, 'shot_*.mp4')))
durs = [float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f])) for f in files]
XF = 0.7
inputs = sum([['-i', f] for f in files], []) + ['-i', os.path.join(V, 'soundtrack.wav')]
fc, prev, off = [], '[0:v]', 0.0
for i in range(1, len(files)):
    off += durs[i - 1] - XF
    lab = f'[x{i}]'
    fc.append(f'{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}{lab}')
    prev = lab
total = off + durs[-1]
fc.append(f'{prev}fade=t=in:st=0:d=1.2,fade=t=out:st={total - 1.8:.3f}:d=1.8[v]')
subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-map', f'{len(files)}:a',
                       '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                       '-c:a', 'aac', '-b:a', '192k', '-shortest', OUTF])
print(OUTF, round(total, 2), 's', os.path.getsize(OUTF) // 1024 // 1024, 'MB')
