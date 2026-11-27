"""Join proposal clips with 0.5 s crossfades, fade in/out, add the score -> deliverables/Drone_Trg_Complex_44_Div_Proposal.mp4"""
import glob, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, '..', 'build', 'proposal3')
OUTF = os.path.join(HERE, '..', 'deliverables', 'Drone_Trg_Complex_44_Div_Proposal_v3.mp4')
files = sorted(glob.glob(os.path.join(V, 'clip_*.mp4')))
assert len(files) == 15, files
durs = [float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f])) for f in files]
XF = 0.5
inputs = sum([['-i', f] for f in files], []) + ['-i', os.path.join(V, 'soundtrack.wav')]
fc, prev, off = [], '[0:v]', 0.0
for i in range(1, len(files)):
    off += durs[i - 1] - XF
    fc.append(f'{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]'); prev = f'[x{i}]'
total = off + durs[-1]
fc.append(f'{prev}fade=t=in:st=0:d=0.8,fade=t=out:st={total - 1.0:.3f}:d=1.0[v]')
subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-map', f'{len(files)}:a',
                       '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-tune', 'film', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                       '-c:a', 'aac', '-b:a', '192k', '-shortest', OUTF])
print(OUTF, round(total, 2), 's', os.path.getsize(OUTF) // 1024 // 1024, 'MB')
