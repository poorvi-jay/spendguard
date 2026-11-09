#!/usr/bin/env bash
# Cuts the waiting out of the real takes (never an outcome) and writes 1920x1080 30 fps clips.
# Cut: agent thinking, PayPal's login screen (shows the sandbox email), PayPal processing,
# and the landing-page flash after PayPal redirects back. Usage: edit_live.sh <folder with the .webm takes>
set -e
F="$LOCALAPPDATA/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin"
cd "${1:-$(dirname "$0")/raw}"
OUT=/c/Users/poorv/spendGuard/video/assets/clips

build() {
  local src=$1 dst=$2; shift 2
  local fc="" n=0
  while [ $# -gt 0 ]; do
    fc="$fc[0:v]trim=start=$1:end=$2,setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,fps=30,setsar=1[s$n];"
    n=$((n+1)); shift 2
  done
  local inputs=""; for i in $(seq 0 $((n-1))); do inputs="$inputs[s$i]"; done
  "$F/ffmpeg" -v error -y -i "$src" -filter_complex "$fc${inputs}concat=n=$n:v=1:a=0[out]" -map "[out]" \
    -c:v libx264 -crf 16 -pix_fmt yuv420p "$OUT/$dst"
  echo "$dst $("$F/ffprobe" -v error -show_entries format=duration -of csv=p=0 "$OUT/$dst")"
}

# typing → pending card + agent reply → PayPal checkout → guard's decision
build approve.webm live-approve.mp4  4.5 8   21.5 24.5  48.5 51  64 68.5
build nudge.webm   live-nudge.mp4    4.5 7.5  17.5 23   34 37    58.5 61  72 76.5
build block.webm   live-block.mp4    24 27.5  36 39     54.5 57  69.3 74
# Ledger: start once the page has jumped to the ledger, hold the last frame to 10 s.
"$F/ffmpeg" -v error -y -ss 4.9 -i ledger.webm -vf "scale=1920:1080:flags=lanczos,fps=30,setsar=1,tpad=stop_mode=clone:stop_duration=2"   -t 10 -an -c:v libx264 -crf 16 -pix_fmt yuv420p "$OUT/ledger.mp4"
