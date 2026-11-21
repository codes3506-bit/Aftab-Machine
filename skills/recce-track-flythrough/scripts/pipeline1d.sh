cd /home/user/recce/work
VID=1 ../venv/bin/python hud2.py ../out/terrain1v3.mp4 ../out/hud1v5.mp4 > ../out/hud1d.log 2>&1
bash finish2.sh hud1v5.mp4 soundtrack1.wav Recce_Altn_Tr_Const_B3_to_Haryaan_BOO_v5 >> ../out/hud1d.log 2>&1
echo PIPE1DONE >> ../out/hud1d.log
