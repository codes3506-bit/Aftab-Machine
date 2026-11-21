cd /home/user/recce/work
until grep -q "^done" ../out/render1t.log; do sleep 15; done
../venv/bin/python - <<'P'
import json
a=json.load(open('/home/user/recce/out/terrain_cams.json')); b=json.load(open('/home/user/recce/out/terrain1_tail_cams.json'))
n=113*30; json.dump(a[:n]+b,open('/home/user/recce/out/terrain1v2_cams.json','w')); print(len(a[:n]+b))
P
ffmpeg -y -v error -i ../out/terrain.mp4 -i ../out/terrain1_tail.mp4 -filter_complex "[0:v]trim=end_frame=3390,setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1[v]" -map "[v]" -c:v libx264 -preset fast -crf 10 -pix_fmt yuv444p ../out/terrain1v2.mp4
VID=1 ../venv/bin/python hud2.py ../out/terrain1v2.mp4 ../out/hud1v2.mp4 > ../out/hud1.log 2>&1
bash finish2.sh hud1v2.mp4 soundtrack1.wav Recce_Altn_Tr_Const_B3_to_Haryaan_BOO_v2 >> ../out/hud1.log 2>&1
echo PIPE1DONE >> ../out/hud1.log
