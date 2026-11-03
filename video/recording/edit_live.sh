#!/usr/bin/env bash
# Cuts the waiting out of the two real takes (never an outcome) and writes 1920x1080 30 fps clips.
set -e
F="$LOCALAPPDATA/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin"
cd "$(dirname "$0")/raw"
OUT=/c/Users/poorv/spendGuard/video/assets/clips

# Segment = start end mode; "pp" punches in 1.5x on PayPal's centred payment panel.
build() {
  local src=$1 dst=$2; shift 2
  local fc="" n=0
  while [ $# -gt 0 ]; do
    local a=$1 b=$2 m=$3; shift 3
    local v="trim=start=$a:end=$b,setpts=PTS-STARTPTS"
    if [ "$m" = pp ]; then v="$v,crop=1066:600:267:300"; fi
    fc="$fc[0:v]$v,scale=1920:1080:flags=lanczos,fps=30,setsar=1[s$n];"
    n=$((n+1))
  done
  local inputs=""; for i in $(seq 0 $((n-1))); do inputs="$inputs[s$i]"; done
  fc="$fc${inputs}concat=n=$n:v=1:a=0[out]"
  "$F/ffmpeg" -v error -y -i "$src" -filter_complex "$fc" -map "[out]" -c:v libx264 -crf 16 -pix_fmt yuv420p "$OUT/$dst"
  "$F/ffprobe" -v error -show_entries format=duration -of csv=p=0 "$OUT/$dst"
}

build approve.webm live-approve.mp4 4 7 app  16.5 21.5 app  30.5 33 app  85.5 88 pp  97 101.5 app
build nudge.webm   live-nudge.mp4   4.5 7.5 app  13.5 17.5 app  17.5 19.5 app  24.5 27.5 app  91 94 pp  102 106.5 app
"$F/ffmpeg" -v error -y -i ledger.webm -vf "scale=1920:1080:flags=lanczos,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$OUT/ledger.mp4"
"$F/ffprobe" -v error -show_entries format=duration -of csv=p=0 "$OUT/ledger.mp4"
