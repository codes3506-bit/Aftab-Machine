cd /home/user/recce/work
until grep -q "ALLDONE" ../out/render2.log 2>/dev/null; do sleep 20; done

VID=2 ../venv/bin/python hud2.py ../out/terrain2.mp4 ../out/hud2v.mp4 > ../out/hud2.log 2>&1
bash finish2.sh hud2v.mp4 soundtrack2.wav Proposed_Altn_Tr_Opt2_B3_to_Haryaan_BOO >> ../out/hud2.log 2>&1
echo PIPE2DONE >> ../out/hud2.log
