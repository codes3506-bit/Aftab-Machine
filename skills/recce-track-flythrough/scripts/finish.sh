#!/bin/bash
# mux HUD video + soundtrack, two-pass to ~2.6 Mb/s (≈ 50 MB for 152 s) plus a high-quality master
set -e
cd /home/user/recce/out
ffmpeg -y -v error -i hud.mp4 -i soundtrack.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart master.mp4
ffmpeg -y -v error -i hud.mp4 -c:v libx264 -preset slow -b:v 2400k -pass 1 -an -f null /dev/null
ffmpeg -y -v error -i hud.mp4 -i soundtrack.wav -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 2400k -pass 2 -c:a aac -b:a 160k -shortest -movflags +faststart "Recce_Altn_Tr_Const_B3_to_Haryaan_BOO.mp4"
ffmpeg -v error -i "Recce_Altn_Tr_Const_B3_to_Haryaan_BOO.mp4" -f null - && echo DECODE_OK
ls -la
