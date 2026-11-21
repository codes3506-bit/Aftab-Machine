#!/bin/bash
# usage: finish2.sh HUD.mp4 SOUND.wav OUTNAME   -> 1080p two-pass (~49 MB) + 720p
set -e
cd /home/user/recce/out
ffmpeg -y -v error -i "$1" -c:v libx264 -preset slow -b:v 2400k -pass 1 -passlogfile p_$3 -an -f null /dev/null
ffmpeg -y -v error -i "$1" -i "$2" -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 2400k -pass 2 -passlogfile p_$3 -c:a aac -b:a 160k -shortest -movflags +faststart "$3.mp4"
ffmpeg -y -v error -i "$3.mp4" -vf scale=1280:720 -c:v libx264 -preset medium -b:v 950k -c:a aac -b:a 128k -movflags +faststart "$3_720p.mp4"
ffmpeg -v error -i "$3.mp4" -f null - && echo DECODE_OK $3
